from sqlalchemy.orm import Session
from models.emergency_contact import EmergencyContact

def get_emergency_contacts(db: Session, user_id: int):
    """Get emergency contacts for a user"""
    return db.query(EmergencyContact).filter(
        EmergencyContact.user_id == user_id
    ).order_by(EmergencyContact.priority).all()

def create_mock_emergency_contacts(db: Session):
    """Create mock emergency contacts if they don't exist"""
    # Check if contacts already exist
    if db.query(EmergencyContact).count() > 0:
        return
    
    # Contacts for User 1 (haile)
    contact1_1 = EmergencyContact(
        user_id=1,
        priority=1,
        contact_name="Maria Selassie",
        relationship="Wife",
        phone="+251949867668",
        whatsapp="+251949867668"
    )
    
    contact1_2 = EmergencyContact(
        user_id=1,
        priority=2,
        contact_name="David Selassie",
        relationship="Brother",
        phone="+251911234569",
        whatsapp="+251911234569"
    )
    
    # Contacts for User 2 (traveler1)
    contact2_1 = EmergencyContact(
        user_id=2,
        priority=1,
        contact_name="Sarah Traveler",
        relationship="Mother",
        phone="+12125551235",
        whatsapp="+12125551235"
    )
    
    contact2_2 = EmergencyContact(
        user_id=2,
        priority=2,
        contact_name="Mike Traveler",
        relationship="Father",
        phone="+12125551236",
        whatsapp="+12125551236"
    )
    
    db.add(contact1_1)
    db.add(contact1_2)
    db.add(contact2_1)
    db.add(contact2_2)
    db.commit()

def update_emergency_contacts(db: Session, user_id: int, contacts_data: list):
    """Update emergency contacts for a user"""
    # Delete existing contacts
    db.query(EmergencyContact).filter(
        EmergencyContact.user_id == user_id
    ).delete()
    
    # Create new contacts
    new_contacts = []
    for contact_data in contacts_data:
        contact = EmergencyContact(
            user_id=user_id,
            priority=contact_data.priority,
            contact_name=contact_data.contact_name,
            relationship=contact_data.relationship,
            phone=contact_data.phone,
            whatsapp=contact_data.whatsapp
        )
        new_contacts.append(contact)
        db.add(contact)
    
    db.commit()
    return new_contacts
