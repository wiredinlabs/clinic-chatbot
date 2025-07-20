import json
import asyncio
from datetime import date, datetime, timedelta, time as dt_time
from typing import Dict, Any, List, Optional, Tuple
from zoneinfo import ZoneInfo

# Google Calendar imports
try:
    from google.oauth2.service_account import Credentials
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
    GOOGLE_AVAILABLE = True
except ImportError:
    GOOGLE_AVAILABLE = False

from app.config.settings import settings

class CalendarService:
    def __init__(self):
        self.credentials = None
        self.service = None
        self.calendar_timezone = 'UTC'
        self._initialize_service()

    def _initialize_service(self):
        """Initialize Google Calendar service"""
        try:
            if not GOOGLE_AVAILABLE:
                print("❌ Google Calendar libraries not installed.")
                return

            import os
            creds_file = settings.google_calendar_credentials_file

            if not os.path.exists(creds_file):
                print(f"❌ Google Calendar credentials file not found at {creds_file}.")
                return

            self.credentials = Credentials.from_service_account_file(
                creds_file,
                scopes=['https://www.googleapis.com/auth/calendar']
            )
            self.service = build('calendar', 'v3', credentials=self.credentials)

            calendar_settings = self.service.calendars().get(calendarId='primary').execute()
            self.calendar_timezone = calendar_settings.get('timeZone', 'UTC')

            print("✅ Google Calendar service initialized")
            print(f"📍 Calendar timezone: {self.calendar_timezone}")

        except Exception as e:
            print(f"❌ Failed to initialize calendar service: {e}")
            self.service = None

    def _find_doctor_for_service(self, service: str, clinic_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Find the appropriate doctor for a given service"""
        if not clinic_data or 'Doctors' not in clinic_data:
            return None
        
        service_lower = service.lower()
        # print(f"🔍 Looking for doctor who provides service: '{service}'")
        
        for doctor in clinic_data['Doctors']:
            doctor_services = doctor.get('Services', {})
            # print(f"   Checking Dr. {doctor.get('Name')}: {list(doctor_services.keys())}")
            
            # Check for exact match first
            for available_service in doctor_services:
                if available_service.lower() == service_lower:
                    # print(f"✅ Found exact match: Dr. {doctor.get('Name')} provides '{available_service}'")
                    return doctor
            
            # Check for partial match
            for available_service in doctor_services:
                if service_lower in available_service.lower() or available_service.lower() in service_lower:
                    # print(f"✅ Found partial match: Dr. {doctor.get('Name')} provides '{available_service}' for requested '{service}'")
                    return doctor
        
        print(f"❌ No doctor found for service: '{service}'")
        return None

    def _get_service_duration(self, doctor: Dict[str, Any], service: str) -> Tuple[int, str]:
        """Get service duration from doctor's services"""
        services = doctor.get('Services', {})
        service_lower = service.lower()
        
        # Check for exact match first
        for available_service, duration_str in services.items():
            if available_service.lower() == service_lower:
                try:
                    duration_minutes = int(duration_str.split()[0])
                    # print(f"✅ Service '{available_service}' duration: {duration_minutes} minutes")
                    return duration_minutes, available_service
                except (ValueError, IndexError):
                    print(f"⚠️ Could not parse duration for '{available_service}': {duration_str}")
                    return 30, available_service
        
        # Check for partial match
        for available_service, duration_str in services.items():
            if service_lower in available_service.lower() or available_service.lower() in service_lower:
                try:
                    duration_minutes = int(duration_str.split()[0])
                    # print(f"✅ Service '{available_service}' (matched '{service}') duration: {duration_minutes} minutes")
                    return duration_minutes, available_service
                except (ValueError, IndexError):
                    # print(f"⚠️ Could not parse duration for '{available_service}': {duration_str}")
                    return 30, available_service
        
        print(f"⚠️ Service '{service}' not found, using default 30 minutes")
        return 30, service

    def _parse_clinic_hours(self, clinic_data: Dict[str, Any]) -> Tuple[int, int]:
        """Parse clinic working hours from clinic data"""
        try:
            # Method 1: Check config.working_hours
            config = clinic_data.get('config', {})
            working_hours = config.get('working_hours', {})
            
            if 'start' in working_hours and 'end' in working_hours:
                start_time = working_hours['start']  # e.g., "09:00"
                end_time = working_hours['end']      # e.g., "18:00"
                
                start_hour = int(start_time.split(':')[0])
                end_hour = int(end_time.split(':')[0])
                
                # print(f"📅 Clinic hours from config: {start_hour}:00 - {end_hour}:00")
                return start_hour, end_hour
            
            # Method 2: Use default from settings
            start_hour = settings.default_start_hour
            end_hour = settings.default_end_hour
            # print(f"📅 Using default clinic hours: {start_hour}:00 - {end_hour}:00")
            return start_hour, end_hour
            
        except Exception as e:
            print(f"❌ Error parsing clinic hours: {e}, using default 9AM-7PM")
            return 9, 19

    async def get_available_slots(
        self, 
        service: str,
        date_str: str, 
        clinic_data: Dict[str, Any] = None,
        clinic_timezone: str = "Asia/Karachi"
    ) -> List[Dict[str, Any]]:
        """Get available slots for a service (finds appropriate doctor automatically)"""
        try:
            # Parse the target date
            if 'T' in date_str:
                target_date = datetime.fromisoformat(date_str.replace('Z', '+00:00')).date()
            else:
                target_date = datetime.fromisoformat(date_str).date()

            # print(f"🗓 Getting slots for {target_date} (service: {service})")
            
            # Find the right doctor for this service
            doctor = self._find_doctor_for_service(service, clinic_data)
            if not doctor:
                print(f"❌ No doctor found for service '{service}'")
                return []
            
            doctor_email = doctor.get('Calendar_email')
            if not doctor_email:
                print(f"❌ No calendar email found for Dr. {doctor.get('Name')}")
                return []
            
            # Get service duration
            duration_minutes, actual_service = self._get_service_duration(doctor, service)
            
            # print(f"📧 Using Dr. {doctor.get('Name')} ({doctor_email})")
            # print(f"🕐 Service duration: {duration_minutes} minutes")

            # if not self.service:
            #     print("⚠️ No real calendar service - generating default slots")
            #     return self._generate_default_slots(target_date, duration_minutes, clinic_timezone, clinic_data)
            
            return await self._get_real_calendar_slots(
                doctor_email, target_date, duration_minutes, clinic_timezone, clinic_data
            )

        except Exception as e:
            print(f"❌ Error getting available slots: {e}")
            return []

    async def _get_real_calendar_slots(
        self, 
        doctor_email: str, 
        target_date: datetime.date, 
        duration_minutes: int,
        clinic_timezone: str,
        clinic_data: Dict[str, Any] = None
    ) -> List[Dict[str, Any]]:
        """Get real calendar slots from Google Calendar"""
        try:
            clinic_tz = ZoneInfo(clinic_timezone)
            utc_tz = ZoneInfo("UTC")

            # Get clinic hours
            start_hour, end_hour = self._parse_clinic_hours(clinic_data or {})

            # Create time range in clinic timezone, then convert to UTC
            start_time_local = datetime.combine(target_date, dt_time(start_hour, 0), tzinfo=clinic_tz)
            end_time_local = datetime.combine(target_date, dt_time(end_hour, 0), tzinfo=clinic_tz)
            
            start_time_utc = start_time_local.astimezone(utc_tz)
            end_time_utc = end_time_local.astimezone(utc_tz)

            # print(f"🔍 Checking calendar: {doctor_email}")
            # print(f"📅 Date range: {start_time_local} to {end_time_local} (local)")

            # Query Google Calendar freebusy API
            freebusy_query = {
                'timeMin': start_time_utc.isoformat(),
                'timeMax': end_time_utc.isoformat(),
                'items': [{'id': doctor_email}],
                'timeZone': 'UTC'
            }

            freebusy_result = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.service.freebusy().query(body=freebusy_query).execute()
            )

            # Parse busy periods
            calendar_data = freebusy_result.get('calendars', {})
            doctor_calendar = calendar_data.get(doctor_email, {})
            busy_periods_raw = doctor_calendar.get('busy', [])
            
            busy_periods = []
            for busy in busy_periods_raw:
                try:
                    busy_start = datetime.fromisoformat(busy['start'].replace('Z', '+00:00'))
                    busy_end = datetime.fromisoformat(busy['end'].replace('Z', '+00:00'))
                    busy_periods.append((busy_start, busy_end))
                    
                    busy_start_local = busy_start.astimezone(clinic_tz)
                    busy_end_local = busy_end.astimezone(clinic_tz)
                    # print(f"📛 BUSY: {busy_start_local.strftime('%I:%M %p')} - {busy_end_local.strftime('%I:%M %p')}")
                except Exception as e:
                    print(f"❌ Error parsing busy period: {e}")

            # Generate and filter slots
            all_slots = self._generate_time_slots(target_date, duration_minutes, clinic_timezone, clinic_data)
            available_slots = []
            
            for slot in all_slots:
                slot_start_utc = datetime.fromisoformat(slot['datetime_utc'])
                slot_end_utc = slot_start_utc + timedelta(minutes=duration_minutes)

                # Check conflicts with busy periods
                is_free = True
                for busy_start, busy_end in busy_periods:
                    if slot_start_utc < busy_end and slot_end_utc > busy_start:
                        is_free = False
                        break

                if is_free:
                    available_slots.append(slot)

            # print(f"📊 Found {len(available_slots)} free slots of {duration_minutes}min each")
            return available_slots
            
        except Exception as e:
            print(f"❌ Error getting real calendar slots: {e}")
            # return self._generate_default_slots(target_date, duration_minutes, clinic_timezone, clinic_data)
            return []  # Return empty list if error occurs

    def _generate_time_slots(
        self, 
        date: datetime.date, 
        duration_minutes: int,
        clinic_timezone: str = "Asia/Karachi",
        clinic_data: Dict[str, Any] = None
    ) -> List[Dict[str, Any]]:
        """Generate time slots for a given date (only future slots for today)"""
        slots = []
        clinic_tz = ZoneInfo(clinic_timezone)
        utc_tz = ZoneInfo("UTC")
        
        start_hour, end_hour = self._parse_clinic_hours(clinic_data or {})
        
        # Get current time in clinic timezone
        now_local = datetime.now(clinic_tz)
        today_date = now_local.date()
        
        # Set initial start time
        current_time_local = datetime.combine(date, dt_time(start_hour, 0), tzinfo=clinic_tz)
        end_time_local = datetime.combine(date, dt_time(end_hour, 0), tzinfo=clinic_tz)
        
        # If the date is today, start from current time or next slot
        if date == today_date:
            # Round up to next slot time (add buffer for booking)
            current_hour = now_local.hour
            current_minute = now_local.minute
            
            # Add 30-minute buffer for booking preparation
            buffer_time = now_local + timedelta(minutes=30)
            
            # Round up to next slot boundary
            next_slot_minute = ((buffer_time.minute // duration_minutes) + 1) * duration_minutes
            
            if next_slot_minute >= 60:
                next_hour = buffer_time.hour + 1
                next_minute = next_slot_minute - 60
            else:
                next_hour = buffer_time.hour
                next_minute = next_slot_minute
            
            # Don't start before clinic opening time
            if next_hour < start_hour:
                next_hour = start_hour
                next_minute = 0
            
            # If we're past clinic hours, no slots for today
            if next_hour >= end_hour:
                # print(f"⏰ Current time ({now_local.strftime('%I:%M %p')}) is past clinic hours. No slots available for today.")
                return []
            
            current_time_local = datetime.combine(date, dt_time(next_hour, next_minute), tzinfo=clinic_tz)
            # print(f"⏰ Today's slots start from {current_time_local.strftime('%I:%M %p')} (current time: {now_local.strftime('%I:%M %p')})")
        
        # Generate slots from current_time_local onwards
        while current_time_local < end_time_local:
            slot_end_local = current_time_local + timedelta(minutes=duration_minutes)
            
            # Make sure slot doesn't extend beyond clinic hours
            if slot_end_local > end_time_local:
                # print(f"🚫 Slot {current_time_local.strftime('%I:%M %p')} would extend beyond clinic hours ({end_hour}:00), stopping")
                break
            
            current_time_utc = current_time_local.astimezone(utc_tz)
            
            # Format for display
            formatted_date = current_time_local.strftime('%A, %B %d')
            formatted_time_only = current_time_local.strftime('%I:%M %p')
            timezone_abbr = current_time_local.strftime('%Z') or clinic_timezone.split('/')[-1]
            
            slots.append({
                'start_time': current_time_local.strftime('%H:%M'),
                'end_time': slot_end_local.strftime('%H:%M'),
                'datetime_utc': current_time_utc.isoformat(),
                'datetime_local': current_time_local.isoformat(),
                'formatted_time': f"{formatted_date} at {formatted_time_only}",
                'formatted_date': formatted_date,
                'formatted_time_only': formatted_time_only,
                'timezone': clinic_timezone,
                'timezone_display': f"{formatted_time_only} {timezone_abbr}",
                'duration_minutes': duration_minutes
            })
            
            # print(f"🕐 Generated slot: {formatted_time_only} - {slot_end_local.strftime('%I:%M %p')} ({duration_minutes}min)")
            current_time_local += timedelta(minutes=duration_minutes)

        return slots

    async def book_appointment(
        self,
        service: str,
        patient_name: str,
        patient_phone: str,
        appointment_datetime: str,
        clinic_data: Dict[str, Any] = None,
        clinic_timezone: str = "Asia/Karachi"
    ) -> Dict[str, Any]:
        """Book appointment for a service (finds appropriate doctor automatically)"""
        try:
            
            # Find the right doctor for this service
            doctor = self._find_doctor_for_service(service, clinic_data)
            if not doctor:
                return {
                    "success": False,
                    "error": f"No doctor found who provides '{service}'"
                }
            
            doctor_email = doctor.get('Calendar_email')
            if not doctor_email:
                return {
                    "success": False,
                    "error": f"No calendar email found for Dr. {doctor.get('Name')}"
                }
            
            # Get service duration
            duration_minutes, actual_service = self._get_service_duration(doctor, service)

            return await self._book_real_appointment(
                doctor_email, patient_name, patient_phone, 
                appointment_datetime, duration_minutes, actual_service, 
                clinic_data, clinic_timezone, doctor
            )
            
        except Exception as e:
            print(f"❌ Error booking appointment: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    async def _book_real_appointment(
        self,
        doctor_email: str,
        patient_name: str,
        patient_phone: str,
        appointment_datetime: str,
        duration_minutes: int,
        service: str,
        clinic_data: Dict[str, Any],
        clinic_timezone: str,
        doctor: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Book real Google Calendar appointment"""
        try:
            start_time_utc = datetime.fromisoformat(appointment_datetime.replace('Z', '+00:00'))
            end_time_utc = start_time_utc + timedelta(minutes=duration_minutes)
            
            clinic_tz = ZoneInfo(clinic_timezone)
            start_time_local = start_time_utc.astimezone(clinic_tz)
            
            # Create calendar event
            event = {
                'summary': f'{service} - {patient_name}',
                'description': f'''
Patient: {patient_name}
Phone: {patient_phone}
Service: {service}
Duration: {duration_minutes} minutes
Doctor: Dr. {doctor.get('Name')}

Clinic: {clinic_data.get('clinic_name', 'N/A')}
Address: {clinic_data.get('address', 'N/A')}
                '''.strip(),
                'start': {
                    'dateTime': start_time_utc.isoformat(),
                    'timeZone': 'UTC',
                },
                'end': {
                    'dateTime': end_time_utc.isoformat(),
                    'timeZone': 'UTC',
                },
            }

            result = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.service.events().insert(
                    calendarId=doctor_email, 
                    body=event
                ).execute()
            )

            timezone_abbr = start_time_local.strftime('%Z') or clinic_timezone.split('/')[-1]

            # print(f"✅ Calendar event created: {result['id']}")

            return {
                "success": True,
                "event_id": result['id'],
                "event_link": result.get('htmlLink'),
                "appointment_details": {
                    "patient_name": patient_name,
                    "patient_phone": patient_phone,
                    "doctor_name": doctor.get('Name'),
                    "doctor_email": doctor_email,
                    "appointment_time_utc": appointment_datetime,
                    "appointment_time_local": start_time_local.isoformat(),
                    "appointment_display": f"{start_time_local.strftime('%A, %B %d at %I:%M %p')} {timezone_abbr}",
                    "service": service,
                    "duration_minutes": duration_minutes,
                    "timezone": clinic_timezone
                }
            }

        except Exception as e:
            print(f"❌ Calendar booking failed: {e}")
            return {
                "success": False,
                "error": f"Calendar booking failed: {str(e)}"
            }

    def get_status(self) -> Dict[str, Any]:
        """Get service status"""
        return {
            "google_available": GOOGLE_AVAILABLE,
            "service_initialized": self.service is not None,
            "credentials_loaded": self.credentials is not None,
            "calendar_timezone": self.calendar_timezone
        }

# Create global instance
calendar_service = CalendarService()