# app/api/clinics.py
from fastapi import APIRouter, HTTPException
from typing import List
from app.services.supabase_service import supabase_service
from app.utils.functions import get_all_services
from app.models.clinic_models import ClinicResponse, ClinicServicesResponse, CreateClinicRequest

router = APIRouter(prefix="/clinics", tags=["clinics"])

@router.get("/{clinic_id}/services", response_model=ClinicServicesResponse)
async def get_clinic_services(clinic_id: str):
    """Get all available services for a specific clinic"""
    try:
        clinic_data = await supabase_service.get_clinic_data(clinic_id)
        if not clinic_data:
            raise HTTPException(status_code=404, detail=f"Clinic not found: {clinic_id}")
        
        services_info = get_all_services(clinic_data)
        
        return ClinicServicesResponse(
            services=services_info,
            clinic_info={
                "name": clinic_data.get('clinic_name'),
                "timezone": clinic_data.get('timezone'),
                "address": clinic_data.get('address'),
                "phone": clinic_data.get('phone')
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/", response_model=List[ClinicResponse])
async def list_clinics():
    """List all clinics (for admin purposes)"""
    try:
        response = supabase_service.supabase.table('clinics').select('clinic_id, clinic_name, address, phone').execute()
        return [ClinicResponse(**clinic) for clinic in response.data]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/", response_model=ClinicResponse)
async def create_clinic(clinic_data: CreateClinicRequest):
    """Create a new clinic (for admin purposes)"""
    try:
        clinic_response = supabase_service.supabase.table('clinics').insert(clinic_data.dict()).execute()
        
        if not clinic_response.data:
            raise HTTPException(status_code=500, detail="Failed to create clinic")
        
        return ClinicResponse(**clinic_response.data[0])
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))