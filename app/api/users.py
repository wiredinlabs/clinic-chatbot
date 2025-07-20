# app/api/users.py
from fastapi import APIRouter, HTTPException, Query
from typing import List
from app.services.supabase_service import supabase_service
from app.models.user_models import UserHistoryResponse, UserAppointmentsResponse

router = APIRouter(prefix="/users", tags=["users"])

@router.get("/{phone_number}/history", response_model=UserHistoryResponse)
async def get_user_chat_history(phone_number: str, clinic_id: str = Query(...)):
    """Get chat history for a specific user"""
    try:
        user = await supabase_service.get_or_create_user(phone_number, clinic_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        session = await supabase_service.get_chat_session(user['id'], clinic_id)
        if not session:
            return UserHistoryResponse(messages=[], session_id=None, user_id=user['id'])
        
        chat_history = await supabase_service.get_chat_history(session['id'])
        
        return UserHistoryResponse(
            messages=chat_history,
            session_id=session['id'],
            user_id=user['id']
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{phone_number}/appointments", response_model=UserAppointmentsResponse)
async def get_user_appointments(phone_number: str, clinic_id: str = Query(...)):
    """Get appointments for a specific user"""
    try:
        user = await supabase_service.get_or_create_user(phone_number, clinic_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        appointments = await supabase_service.get_user_appointments(user['id'], clinic_id)
        
        return UserAppointmentsResponse(
            appointments=appointments,
            user_id=user['id']
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{phone_number}/history")
async def clear_user_history(phone_number: str, clinic_id: str = Query(...)):
    """Clear chat history for a specific user"""
    try:
        user = await supabase_service.get_or_create_user(phone_number, clinic_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        success = await supabase_service.clear_user_chat_history(user['id'], clinic_id)
        
        if success:
            return {"message": "Chat history cleared successfully"}
        else:
            raise HTTPException(status_code=500, detail="Failed to clear chat history")
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))