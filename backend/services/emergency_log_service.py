from sqlalchemy.orm import Session
from models.emergency_log import EmergencyLog
from typing import List
import json

def create_emergency_log(
    db: Session,
    user_id: int,
    contact_id: int,
    call_sid: str,
    signal_type: str,
    emergency_context: dict
) -> EmergencyLog:
    """Create a new emergency log entry"""
    emergency_log = EmergencyLog(
        user_id=user_id,
        contact_id=contact_id,
        call_sid=call_sid,
        signal_type=signal_type,
        emergency_context=json.dumps(emergency_context),
        call_status='initiated'
    )
    
    db.add(emergency_log)
    db.commit()
    db.refresh(emergency_log)
    
    return emergency_log

def update_emergency_log(
    db: Session,
    log_id: int,
    call_status: str = None,
    call_duration: int = None,
    transcript: str = None
) -> EmergencyLog:
    """Update an existing emergency log entry"""
    log = db.query(EmergencyLog).filter(EmergencyLog.id == log_id).first()
    
    if not log:
        return None
    
    if call_status:
        log.call_status = call_status
    if call_duration is not None:
        log.call_duration = call_duration
    if transcript:
        log.transcript = transcript
    
    db.commit()
    db.refresh(log)
    
    return log

def get_emergency_logs(
    db: Session,
    skip: int = 0,
    limit: int = 100
) -> List[EmergencyLog]:
    """Get emergency logs with pagination"""
    return db.query(EmergencyLog).offset(skip).limit(limit).all()

def get_emergency_log_by_call_sid(
    db: Session,
    call_sid: str
) -> EmergencyLog:
    """Get an emergency log by Vapi call SID"""
    return db.query(EmergencyLog).filter(EmergencyLog.call_sid == call_sid).first()