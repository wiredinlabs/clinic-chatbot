#!/usr/bin/env python3
"""
Supabase Database Setup Script for Multi-Clinic Chatbot
Creates tables and populates with initial clinic data
"""

import os
import json
from datetime import datetime
from supabase import create_client, Client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def get_supabase_client():
    """Initialize Supabase client"""
    url = os.getenv("SUPABASE_URL")
    service_key = os.getenv("SUPABASE_SERVICE_KEY")  # Use service key for admin operations
    
    if not url or not service_key:
        raise ValueError("SUPABASE_URL and SUPABASE_SERVICE_KEY must be set in environment variables")
    
    return create_client(url, service_key)

def create_tables(supabase: Client):
    """Create all necessary tables"""
    
    print("🏗️  Creating tables...")
    
    # Note: In Supabase, you typically create tables via the dashboard or SQL editor
    # This script assumes tables are already created. If you need to create them programmatically,
    # you would use the supabase.rpc() method to call SQL functions.
    
    # For reference, here are the SQL commands you would run in Supabase SQL editor:
    
    sql_commands = [
        """
        -- Enable UUID extension
        CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
        """,
        
        """
        -- Clinics table
        CREATE TABLE IF NOT EXISTS clinics (
            id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
            clinic_id VARCHAR(255) UNIQUE NOT NULL,
            clinic_name VARCHAR(255) NOT NULL,
            phone VARCHAR(50),
            whatsapp_contact VARCHAR(50),
            address TEXT,
            timezone VARCHAR(100) DEFAULT 'Asia/Karachi',
            config JSONB DEFAULT '{}',
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        );
        """,
        
        """
        -- Doctors table
        CREATE TABLE IF NOT EXISTS doctors (
            id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
            clinic_id UUID REFERENCES clinics(id) ON DELETE CASCADE,
            name VARCHAR(255) NOT NULL,
            speciality VARCHAR(255),
            calendar_email VARCHAR(255),
            timings TEXT,
            services JSONB DEFAULT '{}',
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        );
        """,
        
        """
        -- Users table
        CREATE TABLE IF NOT EXISTS users (
            id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
            phone_number VARCHAR(50) NOT NULL,
            clinic_id UUID REFERENCES clinics(id) ON DELETE CASCADE,
            name VARCHAR(255),
            last_active TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(phone_number, clinic_id)
        );
        """,
        
        """
        -- Chat sessions table
        CREATE TABLE IF NOT EXISTS chat_sessions (
            id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
            user_id UUID REFERENCES users(id) ON DELETE CASCADE,
            clinic_id UUID REFERENCES clinics(id) ON DELETE CASCADE,
            session_data JSONB DEFAULT '[]',
            last_message_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        );
        """,
        
        """
        -- Chat messages table
        CREATE TABLE IF NOT EXISTS chat_messages (
            id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
            session_id UUID REFERENCES chat_sessions(id) ON DELETE CASCADE,
            user_id UUID REFERENCES users(id) ON DELETE CASCADE,
            clinic_id UUID REFERENCES clinics(id) ON DELETE CASCADE,
            role VARCHAR(50) NOT NULL, -- 'user', 'assistant', 'tool'
            content TEXT,
            tool_calls JSONB,
            tool_call_id VARCHAR(255),
            function_name VARCHAR(255),
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        );
        """,
        
        """
        -- Appointments table
        CREATE TABLE IF NOT EXISTS appointments (
            id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
            user_id UUID REFERENCES users(id) ON DELETE CASCADE,
            clinic_id UUID REFERENCES clinics(id) ON DELETE CASCADE,
            doctor_id UUID REFERENCES doctors(id) ON DELETE SET NULL,
            patient_name VARCHAR(255) NOT NULL,
            patient_phone VARCHAR(50),
            service VARCHAR(255) NOT NULL,
            appointment_datetime TIMESTAMP WITH TIME ZONE NOT NULL,
            duration_minutes INTEGER DEFAULT 30,
            status VARCHAR(50) DEFAULT 'confirmed',
            calendar_event_id VARCHAR(255),
            calendar_event_link TEXT,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        );
        """,
        
        """
        -- Indexes for better performance
        CREATE INDEX IF NOT EXISTS idx_users_phone_clinic ON users(phone_number, clinic_id);
        CREATE INDEX IF NOT EXISTS idx_chat_messages_session ON chat_messages(session_id);
        CREATE INDEX IF NOT EXISTS idx_appointments_user_clinic ON appointments(user_id, clinic_id);
        CREATE INDEX IF NOT EXISTS idx_appointments_datetime ON appointments(appointment_datetime);
        """
    ]
    
    print("📝 SQL commands to run in Supabase SQL editor:")
    print("=" * 60)
    for i, cmd in enumerate(sql_commands, 1):
        print(f"-- Command {i}")
        print(cmd.strip())
        print()
    
    print("⚠️  Please run these SQL commands in your Supabase dashboard SQL editor first!")
    print("    Then run this script again with --populate-data flag")
    return False

def populate_sample_data(supabase: Client):
    """Populate tables with sample clinic data"""
    
    print("📊 Populating sample data...")
    
    # Sample clinic data matching your structure
    sample_clinic_data = {
        "clinic_id": "temp",
        "clinic_name": "TEMP",
        "phone": "042-35714448",
        "whatsapp_contact": "03458589440",
        "address": "Plot 367, J3, Johar Town, Lahore",
        "timezone": "Asia/Karachi",
        "config": {
            "working_hours": {
                "start": "09:00",
                "end": "19:00"
            }
        },
        "doctors": [
            {
                "name": "Ahmed Khan",
                "speciality": "General Dentist",
                "calendar_email": "ahmed@dentalcare.com",
                "timings": "Mon-Sat: 8AM-8PM, Sun: 10AM-6PM",
                "services": {
                    "Cleaning": "30 min",
                    "Filling": "45 min",
                    "Root Canal": "90 min",
                    "Extraction": "30 min"
                }
            },
            {
                "name": "Sarah Ahmed",
                "speciality": "Pediatric Dentist",
                "calendar_email": "sarah@dentalcare.com",
                "timings": "Mon-Fri: 9AM-5PM, Sat: 9AM-2PM, Sun: Closed",
                "services": {
                    "Kids Cleaning": "25 min",
                    "Kids Checkup": "20 min",
                    "Fluoride Treatment": "15 min"
                }
            }
        ]
    }
    
    try:
        # 1. Insert clinic
        print(f"🏥 Inserting clinic: {sample_clinic_data['clinic_name']}")
        
        clinic_insert_data = {
            "clinic_id": sample_clinic_data["clinic_id"],
            "clinic_name": sample_clinic_data["clinic_name"],
            "phone": sample_clinic_data["phone"],
            "whatsapp_contact": sample_clinic_data["whatsapp_contact"],
            "address": sample_clinic_data["address"],
            "timezone": sample_clinic_data["timezone"],
            "config": sample_clinic_data["config"]
        }
        
        # Check if clinic already exists
        existing_clinic = supabase.table('clinics').select('id').eq('clinic_id', sample_clinic_data['clinic_id']).execute()
        
        if existing_clinic.data:
            print(f"   ✅ Clinic already exists, updating...")
            clinic_response = supabase.table('clinics').update(clinic_insert_data).eq('clinic_id', sample_clinic_data['clinic_id']).execute()
            clinic_uuid = existing_clinic.data[0]['id']
        else:
            print(f"   ✅ Creating new clinic...")
            clinic_response = supabase.table('clinics').insert(clinic_insert_data).execute()
            clinic_uuid = clinic_response.data[0]['id']
        
        print(f"   📋 Clinic UUID: {clinic_uuid}")
        
        # 2. Insert doctors
        print(f"👨‍⚕️ Inserting {len(sample_clinic_data['doctors'])} doctors...")
        
        for doctor_data in sample_clinic_data['doctors']:
            doctor_insert_data = {
                "clinic_id": clinic_uuid,
                "name": doctor_data["name"],
                "speciality": doctor_data["speciality"],
                "calendar_email": doctor_data["calendar_email"],
                "timings": doctor_data["timings"],
                "services": doctor_data["services"]
            }
            
            # Check if doctor already exists
            existing_doctor = supabase.table('doctors').select('id').eq('clinic_id', clinic_uuid).eq('name', doctor_data['name']).execute()
            
            if existing_doctor.data:
                print(f"   ✅ {doctor_data['name']} already exists, updating...")
                doctor_response = supabase.table('doctors').update(doctor_insert_data).eq('id', existing_doctor.data[0]['id']).execute()
            else:
                print(f"   ✅ Creating {doctor_data['name']}...")
                doctor_response = supabase.table('doctors').insert(doctor_insert_data).execute()
            
            # List services for this doctor
            services_list = ', '.join(doctor_data['services'].keys())
            print(f"      Services: {services_list}")
        
        print("\n🎉 Sample data populated successfully!")
        print(f"🔗 Clinic ID: {sample_clinic_data['clinic_id']}")
        print("You can now test your chatbot with this clinic data.")
        
        return True
        
    except Exception as e:
        print(f"❌ Error populating data: {e}")
        return False

def verify_data(supabase: Client):
    """Verify that data was inserted correctly"""
    
    print("🔍 Verifying data...")
    
    try:
        # Check clinics
        clinics = supabase.table('clinics').select('*').execute()
        print(f"   📊 Clinics: {len(clinics.data)}")
        
        for clinic in clinics.data:
            print(f"      - {clinic['clinic_name']} ({clinic['clinic_id']})")
            
            # Check doctors for this clinic
            doctors = supabase.table('doctors').select('*').eq('clinic_id', clinic['id']).execute()
            print(f"        Doctors: {len(doctors.data)}")
            
            for doctor in doctors.data:
                services_count = len(doctor.get('services', {}))
                print(f"          - {doctor['name']} ({doctor['speciality']}) - {services_count} services")
        
        # Check other tables
        users = supabase.table('users').select('id').execute()
        sessions = supabase.table('chat_sessions').select('id').execute()
        messages = supabase.table('chat_messages').select('id').execute()
        appointments = supabase.table('appointments').select('id').execute()
        
        print(f"   📊 Users: {len(users.data)}")
        print(f"   📊 Chat Sessions: {len(sessions.data)}")
        print(f"   📊 Chat Messages: {len(messages.data)}")
        print(f"   📊 Appointments: {len(appointments.data)}")
        
        print("✅ Data verification complete!")
        
    except Exception as e:
        print(f"❌ Error verifying data: {e}")

def main():
    """Main execution function"""
    
    print("🚀 Supabase Setup Script for Multi-Clinic Chatbot")
    print("=" * 50)
    
    try:
        # Initialize Supabase client
        supabase = get_supabase_client()
        print("✅ Connected to Supabase")
        
        # Check command line arguments
        import sys
        
        if len(sys.argv) > 1 and sys.argv[1] == "--populate-data":
            # Populate data (assumes tables exist)
            success = populate_sample_data(supabase)
            if success:
                verify_data(supabase)
        elif len(sys.argv) > 1 and sys.argv[1] == "--verify":
            # Just verify existing data
            verify_data(supabase)
        else:
            # Show table creation commands
            create_tables(supabase)
            print("\n🔧 Usage:")
            print("  python setup_supabase.py                 # Show SQL commands")
            print("  python setup_supabase.py --populate-data # Populate sample data")
            print("  python setup_supabase.py --verify        # Verify existing data")
        
    except Exception as e:
        print(f"❌ Setup failed: {e}")
        return False
    
    return True

if __name__ == "__main__":
    main()