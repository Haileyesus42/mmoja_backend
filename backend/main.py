import asyncio
import json
import logging
import os
import sys
import traceback
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Optional, Any

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from sqlalchemy.orm import Session

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Environment setup
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
env_path = os.path.join(project_root, ".env")
load_dotenv(dotenv_path=env_path)

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import after path setup
from core.database import init_user_db_sync, init_face_db, get_user_db
from database.database import SessionLocal
from models import emergency_contact, travel_history, user
from models.emergency_log import EmergencyLog
from routers import auth_routes, contact_routes, face_recognition, user_routes
from routers.face_liveness_router import router as face_liveness_router
from routers.palm_router import router as palm_router
from services.emergency_log_service import (
    create_emergency_log,
    get_emergency_log_by_call_sid,
    update_emergency_log,
)
from services.vapi_service import make_emergency_call
from services.whatsapp_service import send_emergency_whatsapp


# =============================================================================
# Helper to sanitize validation errors (remove bytes)
# =============================================================================
def sanitize_validation_errors(errors: Any) -> Any:
    """Recursively convert bytes to string representation to avoid JSON serialization errors."""
    if isinstance(errors, bytes):
        return f"<binary data: {len(errors)} bytes>"
    if isinstance(errors, dict):
        return {k: sanitize_validation_errors(v) for k, v in errors.items()}
    if isinstance(errors, (list, tuple)):
        return [sanitize_validation_errors(item) for item in errors]
    return errors


# =============================================================================
# Lifespan context manager
# =============================================================================
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting Umojee Emergency System...")
    try:
        await asyncio.to_thread(init_user_db_sync)
        logger.info("User database initialized")
    except Exception as e:
        logger.error(f"Failed to initialize user database: {e}")
    try:
        await init_face_db()
        logger.info("Face database initialized")
    except Exception as e:
        logger.warning(f"Face database initialization skipped: {e}")
    yield
    logger.info("Shutting down Umojee Emergency System...")


app = FastAPI(
    title="Umojee Emergency System",
    description="Emergency management system API",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

API_PREFIX = "/api/v1"
app.include_router(auth_routes.router, prefix=API_PREFIX)
app.include_router(user_routes.router, prefix=API_PREFIX)
app.include_router(contact_routes.router, prefix=API_PREFIX)
app.include_router(face_recognition.router, prefix=API_PREFIX)
app.include_router(face_liveness_router, prefix=API_PREFIX)
app.include_router(palm_router, prefix=API_PREFIX)

# Static files
frontend_path = os.path.join(os.path.dirname(__file__), "..", "frontend")
if os.path.exists(frontend_path):
    app.mount("/static", StaticFiles(directory=frontend_path), name="static")

    @app.get("/")
    async def root():
        return FileResponse(os.path.join(frontend_path, "index.html"))

    @app.get("/index.html")
    async def index():
        return FileResponse(os.path.join(frontend_path, "index.html"))

    @app.get("/profile.html")
    async def profile():
        return FileResponse(os.path.join(frontend_path, "profile.html"))

    @app.get("/contacts.html")
    async def contacts():
        return FileResponse(os.path.join(frontend_path, "contacts.html"))


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


@app.get(f"{API_PREFIX}/emergency/logs")
async def get_emergency_logs(skip: int = 0, limit: int = 100, db: Session = Depends(get_user_db)):
    def _query():
        return db.query(EmergencyLog).offset(skip).limit(limit).all()
    logs = await asyncio.to_thread(_query)
    return {"logs": logs, "total": len(logs)}


class EmergencySignal(BaseModel):
    type: str
    user_name: str
    signal: str
    timestamp: Optional[str] = None


@app.post(f"{API_PREFIX}/emergency/webhook")
async def emergency_webhook(signal: EmergencySignal):
    db = SessionLocal()
    try:
        def _find_user():
            user_obj = db.query(user.User).filter(user.User.username == signal.user_name).first()
            if not user_obj:
                user_obj = db.query(user.User).filter(user.User.full_name == signal.user_name).first()
            return user_obj
        user_obj = await asyncio.to_thread(_find_user)
        if not user_obj:
            return JSONResponse(status_code=404, content={"status": "error", "message": f"User '{signal.user_name}' not found"})

        def _get_contacts():
            return db.query(emergency_contact.EmergencyContact).filter(
                emergency_contact.EmergencyContact.user_id == user_obj.id
            ).order_by(emergency_contact.EmergencyContact.priority).all()
        contacts = await asyncio.to_thread(_get_contacts)
        if not contacts:
            return JSONResponse(status_code=400, content={"status": "error", "message": "No emergency contacts found"})

        primary_contact = contacts[0]
        secondary_contact = contacts[1] if len(contacts) > 1 else None

        def _get_travel():
            return db.query(travel_history.TravelHistory).filter(
                travel_history.TravelHistory.user_id == user_obj.id
            ).all()
        travel_records = await asyncio.to_thread(_get_travel)

        traveler_data = {
            "name": user_obj.full_name or user_obj.username,
            "phone": user_obj.phone or "Not available",
            "email": user_obj.email or "Not available",
            "current_location": user_obj.current_location or f"{user_obj.current_city or 'Unknown'}, {user_obj.current_country or 'Unknown'}",
            "gps": f"{user_obj.gps_latitude}, {user_obj.gps_longitude}" if user_obj.gps_latitude and user_obj.gps_longitude else "Not available",
            "hotel": user_obj.hotel_name or user_obj.address or "Not specified",
            "address": user_obj.address or "Not available",
        }
        sos_data = {
            "status": "ACTIVE",
            "signalType": signal.signal,
            "timestamp": signal.timestamp or datetime.now().isoformat(),
            "locationName": traveler_data["current_location"],
            "gps": traveler_data["gps"],
            "nearbyAccommodation": traveler_data["hotel"],
        }
        trip_data = {}
        if travel_records:
            latest = travel_records[0]
            trip_data = {
                "destination": f"{latest.city}, {latest.country}",
                "date": latest.travel_date or "Unknown",
            }
        else:
            trip_data = {"destination": "Unknown", "date": "Unknown"}
        contact_data = {
            "primary": {
                "name": primary_contact.contact_name,
                "relationship": primary_contact.relationship or "Unknown",
                "phone": primary_contact.phone or "Not available",
                "whatsapp": primary_contact.whatsapp or primary_contact.phone,
            },
            "secondary": {
                "name": secondary_contact.contact_name,
                "relationship": secondary_contact.relationship or "Unknown",
                "phone": secondary_contact.phone or "Not available",
                "whatsapp": secondary_contact.whatsapp or secondary_contact.phone,
            } if secondary_contact else None,
        }
        emergency_context_dict = {
            "traveler_name": traveler_data["name"],
            "current_location": traveler_data["current_location"],
            "gps": traveler_data["gps"],
            "hotel": traveler_data["hotel"],
            "traveler_phone": traveler_data["phone"],
            "signal_type": sos_data["signalType"],
            "contact_name": primary_contact.contact_name,
            "relationship": primary_contact.relationship or "Unknown",
            "contact_phone": primary_contact.phone,
        }

        vapi_response = await asyncio.to_thread(
            make_emergency_call,
            primary_contact.phone,
            traveler_data,
            sos_data,
            trip_data,
            contact_data,
            user_obj.id,
            primary_contact.id,
        )
        if vapi_response:
            await asyncio.to_thread(
                create_emergency_log,
                db,
                user_obj.id,
                primary_contact.id,
                vapi_response.get("id"),
                signal.signal,
                emergency_context_dict,
            )
        else:
            try:
                whatsapp_result = await asyncio.to_thread(
                    send_emergency_whatsapp,
                    primary_contact.contact_name,
                    primary_contact.relationship or "Unknown",
                    primary_contact.phone,
                    emergency_context_dict["traveler_name"],
                    emergency_context_dict["current_location"],
                    emergency_context_dict["gps"],
                    emergency_context_dict["hotel"],
                    signal.signal,
                )
                if whatsapp_result and whatsapp_result.get("success"):
                    await asyncio.to_thread(
                        create_emergency_log,
                        db,
                        user_obj.id,
                        primary_contact.id,
                        f"WHATSAPP_{whatsapp_result.get('message_sid', 'fallback')}",
                        signal.signal,
                        emergency_context_dict,
                    )
            except Exception as e:
                logger.error(f"WhatsApp fallback failed: {e}")

        return {"status": "success", "message": "Emergency signal processed", "user_found": True}
    except Exception as e:
        logger.error(f"Emergency webhook error: {e}\n{traceback.format_exc()}")
        return JSONResponse(status_code=500, content={"status": "error", "message": "Internal server error"})
    finally:
        db.close()


@app.post("/api/v1/vapi/webhook")
async def vapi_webhook(request: Request):
    try:
        body = await request.body()
        payload = json.loads(body.decode("utf-8"))
    except Exception as e:
        logger.error(f"Failed to parse VAPI webhook payload: {e}")
        return JSONResponse(status_code=400, content={"status": "error", "message": "Invalid JSON"})

    message = payload.get("message", {})
    event_type = message.get("type", "unknown")
    call_data = message.get("call", {})
    call_id = call_data.get("id", "unknown")
    call_status = message.get("status") or call_data.get("status")
    ended_reason = message.get("endedReason")

    call_answered = None
    if ended_reason:
        answered_reasons = ["normal-call-disconnect", "completed", "answered"]
        not_answered_reasons = ["customer-did-not-answer", "busy", "no-answer", "assistant-error", "timeout"]
        ended_normalized = ended_reason.lower().replace("-", "_")
        if ended_normalized in [r.replace("-", "_") for r in answered_reasons]:
            call_answered = True
        elif ended_normalized in [r.replace("-", "_") for r in not_answered_reasons]:
            call_answered = False

    db = SessionLocal()
    try:
        if event_type in ["status-update", "end-of-call-report"] and call_id != "unknown":
            def _get_log():
                return get_emergency_log_by_call_sid(db, call_id)
            emergency_log = await asyncio.to_thread(_get_log)
            if emergency_log:
                update_kwargs = {"call_status": call_status}
                if message.get("durationSeconds"):
                    update_kwargs["call_duration"] = message.get("durationSeconds")
                def _update():
                    update_emergency_log(db, emergency_log.id, **update_kwargs)
                await asyncio.to_thread(_update)
                transcript = message.get("transcript") or call_data.get("transcript")
                if transcript:
                    def _update_transcript():
                        update_emergency_log(db, emergency_log.id, transcript=transcript)
                    await asyncio.to_thread(_update_transcript)
                if call_answered is False:
                    try:
                        ctx = emergency_log.emergency_context
                        if isinstance(ctx, str):
                            ctx = json.loads(ctx)
                        elif not isinstance(ctx, dict):
                            ctx = {}
                        contact_phone = ctx.get("contact_phone") or ctx.get("phone") or ""
                        if contact_phone:
                            await asyncio.to_thread(
                                send_emergency_whatsapp,
                                ctx.get("contact_name", "Emergency Contact"),
                                ctx.get("relationship", "Unknown"),
                                contact_phone,
                                ctx.get("traveler_name", "Unknown"),
                                ctx.get("current_location", "Unknown"),
                                ctx.get("gps", "Unknown"),
                                ctx.get("hotel", "Unknown"),
                                ctx.get("signal_type", "SOS_BUTTON"),
                            )
                    except Exception as e:
                        logger.error(f"Fallback WhatsApp failed: {e}")
        return {"status": "received"}
    except Exception as e:
        logger.error(f"VAPI webhook error: {e}\n{traceback.format_exc()}")
        return JSONResponse(status_code=500, content={"status": "error", "message": "Internal error"})
    finally:
        db.close()


@app.post("/vapi/webhook")
async def vapi_legacy_webhook(request: Request):
    return await vapi_webhook(request)


# =============================================================================
# FIXED EXCEPTION HANDLERS (critical for your error)
# =============================================================================
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    # Sanitize the error details to remove any binary data
    sanitized_errors = sanitize_validation_errors(exc.errors())
    logger.warning(f"Validation error (sanitized): {sanitized_errors}")
    return JSONResponse(
        status_code=422,
        content={"detail": "Request validation failed", "errors": sanitized_errors},
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}\n{traceback.format_exc()}")
    if isinstance(exc, UnicodeDecodeError):
        return JSONResponse(status_code=400, content={"detail": "Invalid character encoding"})
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})


# =============================================================================
# Run
# =============================================================================
if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=False)