from pydantic import BaseModel
from typing import Optional, List

# User schemas
class UserBase(BaseModel):
    username: str
    full_name: str
    address: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    current_city: Optional[str] = None
    current_country: Optional[str] = None
    hotel_name: Optional[str] = None
    current_location: Optional[str] = None
    gps_latitude: Optional[str] = None
    gps_longitude: Optional[str] = None

class UserCreate(UserBase):
    password: str

class UserResponse(UserBase):
    id: int

    class Config:
        from_attributes = True

class UserLogin(BaseModel):
    username: str
    password: str

class PalmAuthRequest(BaseModel):
    """Request model for palm-based authentication"""
    palm_image: str  # Base64 encoded palm image

class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    current_city: Optional[str] = None
    current_country: Optional[str] = None
    hotel_name: Optional[str] = None
    current_location: Optional[str] = None
    gps_latitude: Optional[str] = None
    gps_longitude: Optional[str] = None

# Emergency Contact schemas
class EmergencyContactBase(BaseModel):
    priority: int
    contact_name: str
    relationship: Optional[str] = None
    phone: Optional[str] = None
    whatsapp: Optional[str] = None

class EmergencyContactResponse(EmergencyContactBase):
    id: int
    user_id: int

    class Config:
        from_attributes = True

class EmergencyContactUpdate(BaseModel):
    contacts: List[EmergencyContactBase]

# Emergency Log schemas
class EmergencyLogBase(BaseModel):
    user_id: int
    contact_id: int
    call_sid: Optional[str] = None
    call_status: Optional[str] = None
    signal_type: Optional[str] = None
    emergency_context: Optional[str] = None
    transcript: Optional[str] = None
    call_duration: Optional[int] = None

class EmergencyLogResponse(EmergencyLogBase):
    id: int
    created_at: Optional[str] = None

    class Config:
        from_attributes = True

# Travel History schemas
class TravelHistoryBase(BaseModel):
    country: str
    city: str
    travel_date: Optional[str] = None

class TravelHistoryResponse(TravelHistoryBase):
    id: int
    user_id: int

    class Config:
        from_attributes = True