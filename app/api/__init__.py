# app/api/__init__.py
"""
API routes module for the multi-clinic chatbot application.

Contains FastAPI routers for:
- Chat endpoints
- User management
- Clinic management  
- Health checks
"""

from . import chat, users, clinics, health

__all__ = ["chat", "users", "clinics", "health"]