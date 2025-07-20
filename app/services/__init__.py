# app/services/__init__.py
"""
Services module for the multi-clinic chatbot application.

Contains business logic services for:
- Supabase database operations
- OpenAI API integration
- Google Calendar integration
"""

from .supabase_service import supabase_service
from .openai_service import openai_service
from .calendar_service import calendar_service

__all__ = ["supabase_service", "openai_service", "calendar_service"]