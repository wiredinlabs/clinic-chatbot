# app/models/clinic_models.py
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class Doctor(BaseModel):
    name: str = Field(..., description="Doctor's full name")
    speciality: str = Field(..., description="Medical speciality")
    calendar_email: str = Field(..., description="Calendar email for bookings")
    timings: str = Field(..., description="Working hours")
    services: Dict[str, str] = Field(..., description="Services with durations")

class Clinic(BaseModel):
    clinic_id: str = Field(..., description="Unique clinic identifier")
    clinic_name: str = Field(..., description="Clinic name")
    phone: str = Field(..., description="Clinic phone number")
    whatsapp_contact: Optional[str] = Field(None, description="WhatsApp number")
    address: str = Field(..., description="Clinic address")
    timezone: str = Field(default="Asia/Karachi", description="Clinic timezone")
    doctors: List[Doctor] = Field(..., description="List of doctors")

class ClinicResponse(BaseModel):
    clinic_id: str
    clinic_name: str
    address: str
    phone: str

class ClinicInfo(BaseModel):
    name: str
    timezone: str
    address: str
    phone: str

class ClinicServicesResponse(BaseModel):
    services: Dict[str, Any]
    clinic_info: ClinicInfo

class CreateClinicRequest(BaseModel):
    clinic_id: str = Field(..., description="Unique clinic identifier")
    clinic_name: str = Field(..., description="Clinic name")
    phone: Optional[str] = Field(None, description="Clinic phone number")
    whatsapp_contact: Optional[str] = Field(None, description="WhatsApp number")
    address: Optional[str] = Field(None, description="Clinic address")
    timezone: str = Field(default="Asia/Karachi", description="Clinic timezone")
    config: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional configuration")

    class Config:
        schema_extra = {
            "example": {
                "clinic_id": "new_clinic_karachi",
                "clinic_name": "New Medical Center",
                "phone": "021-34567890",
                "whatsapp_contact": "03001234567",
                "address": "Block 5, Clifton, Karachi",
                "timezone": "Asia/Karachi",
                "config": {
                    "working_hours": {
                        "start": "09:00",
                        "end": "18:00"
                    }
                }
            }
        }