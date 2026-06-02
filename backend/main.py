from fastapi import FastAPI, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
import sys
import os
from datetime import datetime

from dotenv import load_dotenv

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
env_path = os.path.join(project_root, '.env')
load_dotenv(dotenv_path=env_path)

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.database import init_user_db_sync, init_face_db, get_user_db
from database.database import SessionLocal  # This is now for PostgreSQL
from models import user, emergency_contact, travel_history
from models.emergency_log import EmergencyLog
from routers import auth_routes, user_routes, contact_routes, face_recognition  # Added face_recognition router
from services.user_service import create_mock_users
from services.contact_service import create_mock_emergency_contacts
from services.travel_service import create_mock_travel_history
from services.vapi_service import make_emergency_call
from services.whatsapp_service import send_emergency_whatsapp
from services.emergency_log_service import create_emergency_log, update_emergency_log, get_emergency_log_by_call_sid
from routers.face_liveness_router import router as face_liveness_router
from routers.palm_router import router as palm_router


app = FastAPI(
    title="Umojee Emergency System",
    description="Emergency management system API",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include all routers with /api/v1 prefix to match Flutter app expectations
app.include_router(auth_routes.router, prefix="/api/v1")
app.include_router(user_routes.router, prefix="/api/v1")
app.include_router(contact_routes.router, prefix="/api/v1")
app.include_router(face_recognition.router, prefix="/api/v1")  # Added face recognition router
app.include_router(face_liveness_router, prefix="/api/v1")  # Add prefix to align with other APIs
app.include_router(palm_router, prefix="/api/v1")  # Add prefix to align with other APIs


frontend_path = os.path.join(os.path.dirname(__file__), '..', 'frontend')
if os.path.exists(frontend_path):
    app.mount("/static", StaticFiles(directory=frontend_path), name="static")

    @app.get("/")
    def root():
        return FileResponse(os.path.join(frontend_path, 'index.html'))

    @app.get("/index.html")
    def index():
        return FileResponse(os.path.join(frontend_path, 'index.html'))

    @app.get("/profile.html")
    def profile():
        return FileResponse(os.path.join(frontend_path, 'profile.html'))

    @app.get("/contacts.html")
    def contacts():
        return FileResponse(os.path.join(frontend_path, 'contacts.html'))

from models.emergency_log import EmergencyLog

@app.on_event("startup")
def startup_event():  # Changed back to sync and handle async properly
    # Initialize user database (PostgreSQL - was SQLite before)
    init_user_db_sync()  # Use sync version for PostgreSQL now
    
    # Try to initialize face database (PostgreSQL - might not be available)
    import asyncio
    
    try:
        # Check if we're in an event loop and handle accordingly
        loop = asyncio.get_running_loop()
        # If we're already in a loop, we can't run another asyncio event loop
        # So we'll skip the face DB initialization for now
        print("Warning: Already running in an event loop, skipping face DB initialization")
    except RuntimeError:
        # No event loop running, safe to use asyncio.run
        try:
            asyncio.run(init_face_db())
        except Exception as e:
            print(f"Warning: Could not initialize face recognition database: {e}")
            print("This is OK if PostgreSQL is not installed or configured.")
            print("The app will continue to run without face recognition features.")
    
    # Create mock data for user database
    # Using the new PostgreSQL session
    db = SessionLocal()
    try:
        # Commenting out mock user creation to allow fresh registrations
        # create_mock_users(db)
        # create_mock_emergency_contacts(db)
        # create_mock_travel_history(db)
        pass  # No mock data created
    finally:
        db.close()

@app.get("/health")
def health_check():
    return {"status": "healthy"}

# Using the new PostgreSQL database session
@app.get("/api/v1/emergency/logs")
def get_emergency_logs(skip: int = 0, limit: int = 100, db: Session = Depends(get_user_db)):  # Changed dependency
    logs = db.query(EmergencyLog).offset(skip).limit(limit).all()
    return {"logs": logs, "total": len(logs)}

def generate_emergency_context(user, travel_records, contacts, signal=None):
    latest_travel = travel_records[0] if travel_records else None

    contact_list = []
    for contact in contacts:
        contact_str = f"{contact.contact_name} ({contact.relationship}) - Phone: {contact.phone}"
        if contact.whatsapp:
            contact_str += f", WhatsApp: {contact.whatsapp}"
        contact_list.append(contact_str)

    return f"""
================================================================================
                             EMERGENCY CONTEXT
================================================================================
Traveler Name: {user.full_name or user.username}
Current Location: {user.current_location or f'{user.current_city or "Unknown"}, {user.current_country or "Unknown"}'}
GPS Coordinates: {f'{user.gps_latitude}, {user.gps_longitude}' if user.gps_latitude and user.gps_longitude else 'Not available'}
Hotel/Address: {user.hotel_name or user.address or 'Not specified'}
Phone: {user.phone or 'Not available'}
Email: {user.email or 'Not available'}

TRAVEL DETAILS:
{f'Destination: {latest_travel.city}, {latest_travel.country}' if latest_travel else 'No travel details available'}
{f'Travel Date: {latest_travel.travel_date}' if latest_travel else ''}

EMERGENCY CONTACTS:
{os.linesep.join([f'- {contact}' for contact in contact_list]) if contact_list else 'No emergency contacts available'}

SOS SIGNAL:
Signal Type: {signal.signal if signal else 'Not specified'}
Timestamp: {signal.timestamp if signal and signal.timestamp else datetime.now().isoformat()}

Additional Information:
No additional notes available
================================================================================
"""

class EmergencySignal(BaseModel):
    type: str
    user_name: str
    signal: str
    timestamp: Optional[str] = None

@app.post("/api/v1/emergency/webhook")
def emergency_webhook(signal: EmergencySignal):
    db = SessionLocal()
    try:
        from models.user import User
        user = db.query(User).filter(User.username == signal.user_name).first()
        if not user:
            user = db.query(User).filter(User.full_name == signal.user_name).first()

        if user:
            from models.emergency_contact import EmergencyContact
            contacts = db.query(EmergencyContact).filter(
                EmergencyContact.user_id == user.id
            ).order_by(EmergencyContact.priority).all()

            if contacts:
                primary_contact = contacts[0]
                secondary_contact = contacts[1] if len(contacts) > 1 else None

                from models.travel_history import TravelHistory
                travel_records = db.query(TravelHistory).filter(
                    TravelHistory.user_id == user.id
                ).all()

                traveler_data = {
                    "name": user.full_name or user.username,
                    "phone": user.phone or "Not available",
                    "email": user.email or "Not available",
                    "current_location": user.current_location or f"{user.current_city or 'Unknown'}, {user.current_country or 'Unknown'}",
                    "gps": f"{user.gps_latitude}, {user.gps_longitude}" if user.gps_latitude and user.gps_longitude else "Not available",
                    "hotel": user.hotel_name or user.address or "Not specified",
                    "address": user.address or "Not available"
                }

                sos_data = {
                    "status": "ACTIVE",
                    "signalType": signal.signal,
                    "timestamp": signal.timestamp or datetime.now().isoformat(),
                    "locationName": user.current_location or f"{user.current_city or 'Unknown'}, {user.current_country or 'Unknown'}",
                    "gps": f"{user.gps_latitude}, {user.gps_longitude}" if user.gps_latitude and user.gps_longitude else "Not available",
                    "nearbyAccommodation": user.hotel_name or user.address or "Not specified"
                }

                if travel_records:
                    latest_trip = travel_records[0]
                    trip_data = {
                        "destination": f"{latest_trip.city}, {latest_trip.country}",
                        "date": latest_trip.travel_date or "Unknown"
                    }
                else:
                    trip_data = {"destination": "Unknown", "date": "Unknown"}

                contact_data = {
                    "primary": {
                        "name": primary_contact.contact_name,
                        "relationship": primary_contact.relationship or "Unknown",
                        "phone": primary_contact.phone or "Not available",
                        "whatsapp": primary_contact.whatsapp or primary_contact.phone
                    },
                    "secondary": {
                        "name": secondary_contact.contact_name,
                        "relationship": secondary_contact.relationship or "Unknown",
                        "phone": secondary_contact.phone or "Not available",
                        "whatsapp": secondary_contact.whatsapp or secondary_contact.phone
                    } if secondary_contact else None
                }

                vapi_response = make_emergency_call(
                    phone_number=primary_contact.phone,
                    traveler=traveler_data,
                    sos_data=sos_data,
                    trip_data=trip_data,
                    contact_data=contact_data,
                    user_id=user.id,
                    contact_id=primary_contact.id
                )

                emergency_context_dict = {
                    "traveler_name": traveler_data["name"],
                    "current_location": traveler_data["current_location"],
                    "gps": traveler_data["gps"],
                    "hotel": traveler_data["hotel"],
                    "traveler_phone": traveler_data["phone"],
                    "signal_type": sos_data["signalType"],
                    "contact_name": primary_contact.contact_name,
                    "relationship": primary_contact.relationship or "Unknown",
                    "contact_phone": primary_contact.phone
                }

                if vapi_response:
                    emergency_log = create_emergency_log(
                        db=db,
                        user_id=user.id,
                        contact_id=primary_contact.id,
                        call_sid=vapi_response.get('id'),
                        signal_type=signal.signal,
                        emergency_context=emergency_context_dict
                    )
                else:
                    try:
                        whatsapp_result = send_emergency_whatsapp(
                            contact_name=primary_contact.contact_name,
                            relationship=primary_contact.relationship or "Unknown",
                            phone=primary_contact.phone,
                            traveler_name=emergency_context_dict['traveler_name'],
                            location=emergency_context_dict['current_location'],
                            gps=emergency_context_dict['gps'],
                            hotel=emergency_context_dict['hotel'],
                            signal_type=signal.signal
                        )
                        
                        if whatsapp_result and whatsapp_result.get('success'):
                            emergency_log = create_emergency_log(
                                db=db,
                                user_id=user.id,
                                contact_id=primary_contact.id,
                                call_sid=f"WHATSAPP_{whatsapp_result.get('message_sid', 'fallback')}",
                                signal_type=signal.signal,
                                emergency_context=emergency_context_dict
                            )
                    except Exception as e:
                        print(f"Error sending WhatsApp: {e}")
                        pass

        return {
            "status": "success",
            "message": "Emergency signal received and data retrieved",
            "user_found": user is not None
        }

    except Exception as e:
        print(f"Error in emergency webhook: {e}")  # Added for debugging
        return {"status": "error", "message": str(e)}
    finally:
        db.close()

@app.post("/vapi/webhook")
async def vapi_legacy_webhook(request: Request):
    """Legacy endpoint for VAPI webhook - redirects to the correct path"""
    # Forward the request to the actual endpoint
    return await vapi_webhook(request)

@app.post("/api/v1/vapi/webhook")
async def vapi_webhook(request: Request):
    import json
    body = await request.body()
    payload = json.loads(body.decode('utf-8'))

    message = payload.get('message', {})
    event_type = message.get('type', 'unknown')

    call_data = message.get('call', {})
    call_id = call_data.get('id', 'unknown')
    call_status = message.get('status') or call_data.get('status')
    ended_reason = message.get('endedReason')

    call_answered = None
    if ended_reason:
        answered_reasons = ['normal-call-disconnect', 'completed', 'answered']
        not_answered_reasons = ['customer-did-not-answer', 'busy', 'no-answer', 'assistant-error', 'timeout']
        ended_normalized = ended_reason.lower().replace('-', '_')
        if ended_normalized in [r.replace('-', '_') for r in answered_reasons]:
            call_answered = True
        elif ended_normalized in [r.replace('-', '_') for r in not_answered_reasons]:
            call_answered = False

    db = SessionLocal()
    try:
        if event_type in ['status-update', 'end-of-call-report'] and call_id != 'unknown':
            emergency_log = get_emergency_log_by_call_sid(db, call_id)
            if emergency_log:
                update_kwargs = {'call_status': call_status}
                if message.get('durationSeconds'):
                    update_kwargs['call_duration'] = message.get('durationSeconds')
                update_emergency_log(db, emergency_log.id, **update_kwargs)

                transcript = message.get('transcript') or call_data.get('transcript')
                if transcript:
                    update_emergency_log(db, emergency_log.id, transcript=transcript)

                if call_answered == False:
                    import json as json_module
                    try:
                        context = emergency_log.emergency_context
                        if isinstance(context, str):
                            context = json_module.loads(context)
                        elif not isinstance(context, dict):
                            context = {}
                        contact_phone = context.get('contact_phone') or context.get('phone') or ''
                        if contact_phone:
                            send_emergency_whatsapp(
                                contact_name=context.get('contact_name', 'Emergency Contact'),
                                relationship=context.get('relationship', 'Unknown'),
                                phone=contact_phone,
                                traveler_name=context.get('traveler_name', 'Unknown'),
                                location=context.get('current_location', 'Unknown'),
                                gps=context.get('gps', 'Unknown'),
                                hotel=context.get('hotel', 'Unknown'),
                                signal_type=context.get('signal_type', 'SOS_BUTTON')
                            )
                    except Exception as e:
                        print(f"Error in fallback WhatsApp: {e}")
                        pass
        return {"status": "received"}

    except Exception as e:
        print(f"Error in VAPI webhook: {e}")  # Added for debugging
        return {"status": "error", "message": str(e)}
    finally:
        db.close()

if __name__ == "__main__":
    import uvicorn
    import os
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
