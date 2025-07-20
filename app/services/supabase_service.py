import os
import json
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import uuid
from supabase import create_client, Client
from app.config.settings import settings

class SupabaseService:
    def __init__(self):
        url: str = settings.supabase_url
        key: str = settings.supabase_anon_key
        
        if not url or not key:
            raise ValueError("SUPABASE_URL and SUPABASE_ANON_KEY must be set in environment variables")
        
        self.supabase: Client = create_client(url, key)
        print("✅ Supabase client initialized")

    async def get_clinic_data(self, clinic_id: str) -> Optional[Dict[str, Any]]:
        """
        Fetch clinic data including doctors and services from Supabase
        Returns data in the same format as the original clinic_data.json
        """
        try:
            # Get clinic information
            clinic_response = self.supabase.table('clinics').select('*').eq('clinic_id', clinic_id).execute()
            
            if not clinic_response.data:
                print(f"❌ Clinic not found: {clinic_id}")
                return None
            
            clinic = clinic_response.data[0]
            
            # Get doctors for this clinic
            doctors_response = self.supabase.table('doctors').select('*').eq('clinic_id', clinic['id']).execute()
            
            # Transform to match original format
            clinic_data = {
                "clinic_id": clinic['clinic_id'],
                "clinic_name": clinic['clinic_name'],
                "whatsapp_contact": clinic['whatsapp_contact'],
                "phone": clinic['phone'],
                "address": clinic['address'],
                "timezone": clinic['timezone'],
                "config": clinic.get('config', {}),
                "Doctors": []
            }
            
            # Transform doctors data
            for doctor in doctors_response.data:
                doctor_data = {
                    "Name": doctor['name'],
                    "Speciality": doctor['speciality'],
                    "Calendar_email": doctor['calendar_email'],
                    "Timings": doctor['timings'],
                    "Services": doctor.get('services', {})
                }
                clinic_data["Doctors"].append(doctor_data)
            
            print(f"✅ Loaded clinic data for: {clinic['clinic_name']}")
            return clinic_data
            
        except Exception as e:
            print(f"❌ Error fetching clinic data: {e}")
            return None

    async def get_or_create_user(self, phone_number: str, clinic_id: str, name: str = None) -> Optional[Dict[str, Any]]:
        """
        Get existing user or create new one
        """
        try:
            # First get the clinic UUID
            clinic_response = self.supabase.table('clinics').select('id').eq('clinic_id', clinic_id).execute()
            
            if not clinic_response.data:
                print(f"❌ Clinic not found: {clinic_id}")
                return None
            
            clinic_uuid = clinic_response.data[0]['id']
            
            # Check if user exists
            user_response = self.supabase.table('users').select('*').eq('phone_number', phone_number).eq('clinic_id', clinic_uuid).execute()
            
            if user_response.data:
                # Update last_active
                user = user_response.data[0]
                self.supabase.table('users').update({
                    'last_active': datetime.now().isoformat(),
                    'name': name or user.get('name')
                }).eq('id', user['id']).execute()
                
                print(f"✅ Found existing user: {phone_number}")
                return user
            else:
                # Create new user
                new_user = {
                    'phone_number': phone_number,
                    'clinic_id': clinic_uuid,
                    'name': name,
                    'last_active': datetime.now().isoformat()
                }
                
                user_response = self.supabase.table('users').insert(new_user).execute()
                print(f"✅ Created new user: {phone_number}")
                return user_response.data[0]
                
        except Exception as e:
            print(f"❌ Error managing user: {e}")
            return None

    async def get_chat_session(self, user_id: str, clinic_id: str) -> Optional[Dict[str, Any]]:
        """
        Get the latest chat session for a user or create a new one
        Modified to preserve context indefinitely (no session timeout)
        """
        try:
            clinic_response = self.supabase.table('clinics').select('id').eq('clinic_id', clinic_id).execute()
            
            if not clinic_response.data:
                return None
            
            clinic_uuid = clinic_response.data[0]['id']
            
            # Get the most recent session
            session_response = self.supabase.table('chat_sessions').select('*').eq('user_id', user_id).eq('clinic_id', clinic_uuid).order('last_message_at', desc=True).limit(1).execute()
            
            if session_response.data:
                session = session_response.data[0]
                
                # REMOVED: Session timeout check - always use existing session
                # This preserves chat history indefinitely
                print(f"✅ Using existing session: {session['id']}")
                return session
            
            # Create new session if no session exists (KEEP THIS!)
            # This is essential for new users
            new_session = {
                'user_id': user_id,
                'clinic_id': clinic_uuid,
                'session_data': [],
                'last_message_at': datetime.now().isoformat()
            }
            
            session_response = self.supabase.table('chat_sessions').insert(new_session).execute()
            print(f"✅ Created new chat session")
            return session_response.data[0]
            
        except Exception as e:
            print(f"❌ Error managing chat session: {e}")
            return None
        
    async def save_message(self, session_id: str, user_id: str, clinic_id: str, role: str, content: str, tool_calls: List[Dict] = None, tool_call_id: str = None, function_name: str = None) -> bool:
        """
        Save a message to the database
        """
        try:
            clinic_response = self.supabase.table('clinics').select('id').eq('clinic_id', clinic_id).execute()
            
            if not clinic_response.data:
                return False
            
            clinic_uuid = clinic_response.data[0]['id']
            
            message_data = {
                'session_id': session_id,
                'user_id': user_id,
                'clinic_id': clinic_uuid,
                'role': role,
                'content': content,
                'tool_calls': tool_calls,
                'tool_call_id': tool_call_id,
                'function_name': function_name
            }
            
            self.supabase.table('chat_messages').insert(message_data).execute()
            
            # Update session's last_message_at
            self.supabase.table('chat_sessions').update({
                'last_message_at': datetime.now().isoformat()
            }).eq('id', session_id).execute()
            
            return True
            
        except Exception as e:
            print(f"❌ Error saving message: {e}")
            return False

    async def get_chat_history(self, session_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Get chat history for a session
        """
        try:
            messages_response = self.supabase.table('chat_messages').select('*').eq('session_id', session_id).order('created_at', desc=False).limit(limit).execute()
            
            chat_history = []
            for msg in messages_response.data:
                message = {
                    "role": msg['role'],
                    "content": msg['content']
                }
                
                if msg['tool_calls']:
                    message["tool_calls"] = msg['tool_calls']
                
                if msg['tool_call_id']:
                    message["tool_call_id"] = msg['tool_call_id']
                    message["name"] = msg['function_name']
                
                chat_history.append(message)
            
            print(f"✅ Loaded {len(chat_history)} messages from history")
            return chat_history
            
        except Exception as e:
            print(f"❌ Error loading chat history: {e}")
            return []

    async def save_appointment(self, user_id: str, clinic_id: str, appointment_details: Dict[str, Any]) -> bool:
        """
        Save appointment details to database
        """
        try:
            clinic_response = self.supabase.table('clinics').select('id').eq('clinic_id', clinic_id).execute()
            
            if not clinic_response.data:
                return False
            
            clinic_uuid = clinic_response.data[0]['id']
            
            # Find doctor
            doctor_response = self.supabase.table('doctors').select('id').eq('clinic_id', clinic_uuid).eq('calendar_email', appointment_details.get('doctor_email')).execute()
            
            doctor_id = doctor_response.data[0]['id'] if doctor_response.data else None
            
            appointment_data = {
                'user_id': user_id,
                'clinic_id': clinic_uuid,
                'doctor_id': doctor_id,
                'patient_name': appointment_details.get('patient_name'),
                'patient_phone': appointment_details.get('patient_phone'),
                'service': appointment_details.get('service'),
                'appointment_datetime': appointment_details.get('appointment_time_utc'),
                'duration_minutes': appointment_details.get('duration_minutes'),
                'calendar_event_id': appointment_details.get('event_id'),
                'calendar_event_link': appointment_details.get('event_link'),
                'status': 'confirmed'
            }
            
            self.supabase.table('appointments').insert(appointment_data).execute()
            print(f"✅ Appointment saved to database")
            return True
            
        except Exception as e:
            print(f"❌ Error saving appointment: {e}")
            return False

    async def get_user_appointments(self, user_id: str, clinic_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get user's recent appointments
        """
        try:
            clinic_response = self.supabase.table('clinics').select('id').eq('clinic_id', clinic_id).execute()
            
            if not clinic_response.data:
                return []
            
            clinic_uuid = clinic_response.data[0]['id']
            
            appointments_response = self.supabase.table('appointments').select('*, doctors(name)').eq('user_id', user_id).eq('clinic_id', clinic_uuid).order('appointment_datetime', desc=True).limit(limit).execute()
            
            return appointments_response.data
            
        except Exception as e:
            print(f"❌ Error fetching appointments: {e}")
            return []

    async def clear_user_chat_history(self, user_id: str, clinic_id: str) -> bool:
        """
        Clear chat history for a user (useful for testing or privacy)
        """
        try:
            clinic_response = self.supabase.table('clinics').select('id').eq('clinic_id', clinic_id).execute()
            
            if not clinic_response.data:
                return False
            
            clinic_uuid = clinic_response.data[0]['id']
            
            # Delete all chat messages for the user
            self.supabase.table('chat_messages').delete().eq('user_id', user_id).eq('clinic_id', clinic_uuid).execute()
            
            # Delete all chat sessions for the user
            self.supabase.table('chat_sessions').delete().eq('user_id', user_id).eq('clinic_id', clinic_uuid).execute()
            
            print(f"✅ Cleared chat history for user: {user_id}")
            return True
            
        except Exception as e:
            print(f"❌ Error clearing chat history: {e}")
            return False

    async def update_session_data(self, session_id: str, session_data: List[Dict]) -> bool:
        """
        Update session data (backup method)
        """
        try:
            self.supabase.table('chat_sessions').update({
                'session_data': session_data,
                'last_message_at': datetime.now().isoformat()
            }).eq('id', session_id).execute()
            
            return True
            
        except Exception as e:
            print(f"❌ Error updating session data: {e}")
            return False

# Create global instance
supabase_service = SupabaseService()