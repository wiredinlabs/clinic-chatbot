# app/models/user_models.py
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from .chat_models import ChatMessage

class User(BaseModel):
    id: str
    phone_number: str
    clinic_id: str
    name: Optional[str] = None
    last_active: datetime
    created_at: datetime

class UserHistoryResponse(BaseModel):
    messages: List[ChatMessage]
    session_id: Optional[str]
    user_id: str

class Appointment(BaseModel):
    id: str
    patient_name: str
    patient_phone: str
    service: str
    appointment_datetime: datetime
    duration_minutes: int
    status: str
    doctor_name: Optional[str] = None
    calendar_event_id: Optional[str] = None
    calendar_event_link: Optional[str] = None

class UserAppointmentsResponse(BaseModel):
    appointments: List[Dict[str, Any]]  # Using Dict to handle joined data
    user_id: str