# app/models/__init__.py
"""
Data models module for the multi-clinic chatbot application.

Contains Pydantic models for:
- Chat requests and responses
- User management
- Clinic management
- API data validation
"""

from .chat_models import ChatRequest, ChatResponse, ChatMessage
from .user_models import User, UserHistoryResponse, UserAppointmentsResponse, Appointment
from .clinic_models import Clinic, Doctor, ClinicResponse, ClinicServicesResponse, CreateClinicRequest

__all__ = [
    "ChatRequest", "ChatResponse", "ChatMessage",
    "User", "UserHistoryResponse", "UserAppointmentsResponse", "Appointment",
    "Clinic", "Doctor", "ClinicResponse", "ClinicServicesResponse", "CreateClinicRequest"
]