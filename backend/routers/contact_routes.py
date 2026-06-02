from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from core.database import get_user_db  # Changed to use PostgreSQL database dependency
from schemas.schemas import EmergencyContactResponse, EmergencyContactUpdate
from routers.auth_routes import get_current_user
from services.contact_service import get_emergency_contacts, update_emergency_contacts
from models.user import User

router = APIRouter(prefix="/user/emergency-contacts", tags=["Emergency Contacts"])

@router.get("/", response_model=list[EmergencyContactResponse])
def get_contacts(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_user_db)  # Changed dependency
):
    """Get emergency contacts for logged-in user"""
    user = current_user  # Use the user from dependency injection
    contacts = get_emergency_contacts(db, user.id)
    return contacts

@router.put("/")
def update_contacts(
    contacts_data: EmergencyContactUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_user_db)  # Changed dependency
):
    """Update emergency contacts for logged-in user"""
    user = current_user  # Use the user from dependency injection
    
    updated_contacts = update_emergency_contacts(
        db, 
        user.id, 
        contacts_data.contacts
    )
    
    return {
        "message": "Emergency contacts updated successfully",
        "contacts": [
            {
                "id": contact.id,
                "priority": contact.priority,
                "contact_name": contact.contact_name,
                "relationship": contact.relationship,
                "phone": contact.phone,
                "whatsapp": contact.whatsapp
            }
            for contact in updated_contacts
        ]
    }