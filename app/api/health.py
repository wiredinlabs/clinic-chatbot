# app/api/health.py
from fastapi import APIRouter
from app.services.supabase_service import supabase_service
from app.utils.functions import get_calendar_status

router = APIRouter(prefix="/health", tags=["health"])

@router.get("/")
async def health_check():
    """Health check endpoint"""
    calendar_status = get_calendar_status()
    
    try:
        # Test Supabase connection
        test_clinic = await supabase_service.get_clinic_data("test")
        supabase_status = {"connected": True, "error": None}
    except Exception as e:
        supabase_status = {"connected": False, "error": str(e)}
    
    return {
        "status": "healthy",
        "services": {
            "calendar": calendar_status,
            "supabase": supabase_status
        }
    }

@router.get("/calendar")
async def calendar_status():
    """Get calendar service status"""
    return get_calendar_status()