# app/utils/__init__.py
"""
Utilities module for the multi-clinic chatbot application.

Contains utility functions for:
- Core business logic
- System prompt generation
- Date/time processing
- Data validation
"""

from .functions import (
    available_slots, 
    book_appointment, 
    get_all_services, 
    get_calendar_status,
    find_doctor_for_service,
    validate_service
)
from .prompt import get_system_prompt, validate_clinic_data_structure

__all__ = [
    "available_slots", 
    "book_appointment", 
    "get_all_services", 
    "get_calendar_status",
    "find_doctor_for_service",
    "validate_service",
    "get_system_prompt", 
    "validate_clinic_data_structure"
]