from typing import List, Dict
import datetime
import asyncio
import json
from app.services.calendar_service import calendar_service

def find_doctor_for_service(service: str, clinic_data: Dict = None) -> Dict:
    """
    Find the appropriate doctor for a given service.
    Returns doctor info including email and duration.
    """
    if not clinic_data or 'Doctors' not in clinic_data:
        return {}
    
    service_lower = service.lower()
    print(f"🔍 Looking for doctor who provides service: '{service}'")
    
    for doctor in clinic_data['Doctors']:
        services = doctor.get('Services', {})
        print(f"   Checking Dr. {doctor.get('Name')}: {list(services.keys())}")
        
        # Check for exact match first
        for available_service in services:
            if available_service.lower() == service_lower:
                try:
                    duration_minutes = int(services[available_service].split()[0])
                except:
                    duration_minutes = 30
                
                print(f"✅ Found exact match: Dr. {doctor.get('Name')} provides '{available_service}'")
                return {
                    'name': doctor.get('Name'),
                    'email': doctor.get('Calendar_email'),
                    'speciality': doctor.get('Speciality'),
                    'service_duration': duration_minutes,
                    'found_service': available_service
                }
        
        # Check for partial match
        for available_service in services:
            if service_lower in available_service.lower() or available_service.lower() in service_lower:
                try:
                    duration_minutes = int(services[available_service].split()[0])
                except:
                    duration_minutes = 30
                
                print(f"✅ Found partial match: Dr. {doctor.get('Name')} provides '{available_service}' for requested '{service}'")
                return {
                    'name': doctor.get('Name'),
                    'email': doctor.get('Calendar_email'),
                    'speciality': doctor.get('Speciality'),
                    'service_duration': duration_minutes,
                    'found_service': available_service
                }
    
    print(f"❌ No doctor found for service: '{service}'")
    return {}

async def available_slots(service: str, date: str, clinic_data: Dict = None) -> List[str]:
    """
    Get available appointment slots for a service on a specific date.
    Automatically finds the right doctor for the service.
    """
    try:
        # Parse the date
        appointment_date = datetime.datetime.strptime(date, "%Y-%m-%d")
        date_str = appointment_date.strftime("%Y-%m-%d")
        
        print(f"🔍 Checking available slots for service '{service}' on {date_str}")
        
        # Get clinic timezone from clinic data
        clinic_timezone = clinic_data.get('timezone', 'Asia/Karachi') if clinic_data else 'Asia/Karachi'
        
        # Use the calendar service to get available slots
        # The calendar service will automatically find the right doctor and duration
        slots_data = await calendar_service.get_available_slots(
            service=service,
            date_str=date_str,
            clinic_data=clinic_data,
            clinic_timezone=clinic_timezone
        )
        
        # Convert to the format expected by the system
        formatted_slots = []
        for slot in slots_data:
            # Format: "2025-07-21 09:00 AM"
            formatted_slot = f"{date_str} {slot['formatted_time_only']}"
            formatted_slots.append(formatted_slot)
        
        print(f"✅ Found {len(formatted_slots)} available slots for '{service}'")
        return formatted_slots
        
    except ValueError as e:
        print(f"❌ Date parsing error: {e}")
        return []
    except Exception as e:
        print(f"❌ Error getting available slots: {e}")
        return []

async def book_appointment(
    service: str,
    patient_name: str, 
    slot: str,
    patient_phone: str = "",
    clinic_data: Dict = None
) -> str:
    """
    Book a confirmed appointment for a patient.
    Automatically finds the right doctor for the service.
    """
    try:
        print(f"📅 Booking appointment:")
        print(f"   Service: {service}")
        print(f"   Patient: {patient_name}")
        print(f"   Slot: {slot}")
        
        # Parse the slot datetime
        try:
            slot_datetime = datetime.datetime.strptime(slot, "%Y-%m-%d %I:%M %p")
        except ValueError:
            # Try alternative format: "2025-07-21 09:00"
            slot_datetime = datetime.datetime.strptime(slot, "%Y-%m-%d %H:%M")
        
        # Get clinic timezone
        clinic_timezone = clinic_data.get('timezone', 'Asia/Karachi') if clinic_data else 'Asia/Karachi'
        
        # Convert to UTC for Google Calendar
        from zoneinfo import ZoneInfo
        clinic_tz = ZoneInfo(clinic_timezone)
        utc_tz = ZoneInfo("UTC")
        
        # Create timezone-aware datetime
        slot_datetime_local = slot_datetime.replace(tzinfo=clinic_tz)
        slot_datetime_utc = slot_datetime_local.astimezone(utc_tz)
        
        # Use calendar service to book the appointment
        # The calendar service will automatically find the right doctor and duration
        booking_result = await calendar_service.book_appointment(
            service=service,
            patient_name=patient_name,
            patient_phone=patient_phone,
            appointment_datetime=slot_datetime_utc.isoformat(),
            clinic_data=clinic_data,
            clinic_timezone=clinic_timezone
        )
        
        if booking_result.get("success"):
            appointment_details = booking_result.get("appointment_details", {})
            
            # Get clinic info for confirmation message
            clinic_name = clinic_data.get('clinic_name', 'Skin and Smile Clinic') if clinic_data else 'Skin and Smile Clinic'
            clinic_address = clinic_data.get('address', 'Plot 367, J3, Johar Town, Lahore') if clinic_data else 'Plot 367, J3, Johar Town, Lahore'
            clinic_phone = clinic_data.get('whatsapp_contact', '03458589440') if clinic_data else '03458589440'
            
            doctor_name = appointment_details.get('doctor_name', 'Doctor')
            duration_minutes = appointment_details.get('duration_minutes', 30)
            
            confirmation_message = (
                f"✅ Appointment Confirmed!\n\n"
                f"Patient: {patient_name}\n"
                f"Service: {service}\n"
                f"Duration: {duration_minutes} minutes\n"
                f"Date & Time: {appointment_details.get('appointment_display', slot)}\n"
                f"Doctor: {doctor_name}\n\n"
                f"📍 Location: {clinic_name}\n"
                f"{clinic_address}\n\n"
                f"📞 Contact: {clinic_phone}\n\n"
            )
            
            if booking_result.get("mock_booking"):
                confirmation_message += "⚠️ This is a test booking\n\n"
            
            confirmation_message += "Please arrive 10 minutes early. Thank you!"
            
            print(f"✅ Appointment booked successfully for {duration_minutes} minutes")
            return confirmation_message
        else:
            error_msg = booking_result.get("error", "Unknown error occurred")
            print(f"❌ Booking failed: {error_msg}")
            clinic_phone = clinic_data.get('phone', '03458589440') if clinic_data else '03458589440'
            return f"Sorry, there was an error booking your appointment: {error_msg}. Please try again or call us at {clinic_phone}."
        
    except Exception as e:
        print(f"❌ Error booking appointment: {e}")
        clinic_phone = clinic_data.get('phone', '03458589440') if clinic_data else '03458589440'
        return f"Sorry, there was an error booking your appointment. Please try again or call us at {clinic_phone}."

def get_doctor_info(speciality: str = None, service: str = None, clinic_data: Dict = None) -> Dict:
    """
    Get doctor information based on speciality or service.
    Enhanced to include service durations.
    """
    if not clinic_data or 'Doctors' not in clinic_data:
        # Fallback to hardcoded data
        doctors_info = {
            "dental": {
                "name": "Dr. Azeem Rauf",
                "speciality": "Orthodontist and Dental Surgeon", 
                "email": "minhaljaved10@gmail.com",
                "services": ["Braces", "Cosmetic Fillings", "Dental Implants", "Teeth Whitening"]
            },
            "dermatology": {
                "name": "Dr. Wajeeha Nusrat",
                "speciality": "Dermatologist",
                "email": "minhaljaved10@gmail.com", 
                "services": ["Hydrafacial", "Chemical Peels", "Laser hair removal", "Botox"]
            }
        }
        return doctors_info
    
    # Use clinic data to build doctor info with service durations
    doctors_info = {}
    for doctor in clinic_data['Doctors']:
        doctor_key = doctor.get('Speciality', '').lower().replace(' ', '_').replace('and_', '').replace('surgeon', '').strip('_')
        services_with_duration = {}
        
        for service_name, duration_str in doctor.get('Services', {}).items():
            try:
                duration_minutes = int(duration_str.split()[0])
                services_with_duration[service_name] = {
                    'duration_minutes': duration_minutes,
                    'duration_display': duration_str
                }
            except:
                services_with_duration[service_name] = {
                    'duration_minutes': 30,
                    'duration_display': '30 min'
                }
        
        doctors_info[doctor_key] = {
            "name": doctor.get('Name'),
            "speciality": doctor.get('Speciality'),
            "email": doctor.get('Calendar_email'),
            "timings": doctor.get('Timings'),
            "services": list(doctor.get('Services', {}).keys()),
            "services_with_duration": services_with_duration
        }
    
    return doctors_info

def get_calendar_status() -> Dict:
    """Get calendar service status"""
    return calendar_service.get_status()

def get_all_services(clinic_data: Dict = None) -> Dict:
    """Get all available services with their details"""
    if not clinic_data or 'Doctors' not in clinic_data:
        return {}
    
    services_info = {}
    
    for doctor in clinic_data['Doctors']:
        doctor_name = doctor.get('Name', 'Unknown Doctor')
        doctor_email = doctor.get('Calendar_email', '')
        speciality = doctor.get('Speciality', '')
        timings = doctor.get('Timings', '')
        
        for service_name, duration_str in doctor.get('Services', {}).items():
            try:
                duration_minutes = int(duration_str.split()[0])
            except:
                duration_minutes = 30
            
            services_info[service_name] = {
                'doctor_name': doctor_name,
                'doctor_email': doctor_email,
                'speciality': speciality,
                'timings': timings,
                'duration_minutes': duration_minutes,
                'duration_display': duration_str
            }
    
    return services_info

def validate_service(service: str, clinic_data: Dict = None) -> Dict:
    """
    Validate if a service exists and return service details
    """
    if not clinic_data or 'Doctors' not in clinic_data:
        return {"valid": False, "message": "No clinic data available"}
    
    service_lower = service.lower()
    
    for doctor in clinic_data['Doctors']:
        services = doctor.get('Services', {})
        
        # Check for exact match
        for available_service in services:
            if available_service.lower() == service_lower:
                try:
                    duration_minutes = int(services[available_service].split()[0])
                except:
                    duration_minutes = 30
                
                return {
                    "valid": True,
                    "service_name": available_service,
                    "doctor_name": doctor.get('Name'),
                    "doctor_email": doctor.get('Calendar_email'),
                    "duration_minutes": duration_minutes,
                    "speciality": doctor.get('Speciality')
                }
        
        # Check for partial match
        for available_service in services:
            if service_lower in available_service.lower() or available_service.lower() in service_lower:
                try:
                    duration_minutes = int(services[available_service].split()[0])
                except:
                    duration_minutes = 30
                
                return {
                    "valid": True,
                    "service_name": available_service,
                    "doctor_name": doctor.get('Name'),
                    "doctor_email": doctor.get('Calendar_email'),
                    "duration_minutes": duration_minutes,
                    "speciality": doctor.get('Speciality'),
                    "note": f"Matched '{service}' to '{available_service}'"
                }
    
    # Get list of all available services for suggestion
    all_services = []
    for doctor in clinic_data['Doctors']:
        all_services.extend(list(doctor.get('Services', {}).keys()))
    
    return {
        "valid": False,
        "message": f"Service '{service}' not found",
        "available_services": all_services
    }