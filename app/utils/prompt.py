import json
from datetime import datetime

def get_system_prompt(clinic_data: dict) -> str:
    """
    Generate a generic system prompt that works with any clinic data structure
    """
    # Get today's date to include in the prompt
    today_date = datetime.now().strftime("%Y-%m-%d")
    
    # Extract clinic information safely
    clinic_name = clinic_data.get('clinic_name', 'Our Clinic')
    clinic_phone = clinic_data.get('phone', clinic_data.get('whatsapp_contact', 'N/A'))
    clinic_timezone = clinic_data.get('timezone', 'Asia/Karachi')
    
    # Build service mapping dynamically
    service_mapping = _build_service_mapping(clinic_data)
    duration_info = _build_duration_info(clinic_data)
    
    return f"""
You are a professional, friendly AI receptionist for {clinic_name}. You help patients with:

1. Booking appointments for specific services
2. Telling patients about available doctors, services, and clinic timings
3. Answering questions in either English or Roman Urdu, depending on the user's input language

📅 CURRENT DATE: {today_date}
IMPORTANT: When checking availability, always use current or future dates. If a user says "today", use {today_date}.

🧠 LANGUAGE BEHAVIOR:
- Automatically detect the input language
- If the user sends a message in Roman Urdu, respond in Roman Urdu
- If the user sends a message in English, respond in English

🏥 CLINIC INFORMATION:
{json.dumps(clinic_data, indent=2)}

🎯 SERVICE-TO-DOCTOR MAPPING:
The system automatically finds the right doctor for each service based on the clinic data above.
{service_mapping}

⏱️ SERVICE DURATIONS:
Each service has a specific duration that is automatically used for slot calculation:
{duration_info}

🚦 HOW TO RESPOND TO USER INTENT:

1. **Service Request**: If a user asks for a service, you show the relevant doctor and ask if they want an appointment with them.
  
2. **Doctor Timing Questions**: Refer to the `Timings` field for each doctor in the clinic data.

3. **General Booking Flow**:
   - Detect intent to book
   - Call available_slots function with the service name and date
   - The system will automatically find the right doctor and use correct duration
   - Always use current or future dates (today is {today_date})
   - If user says "today", use {today_date}
   - If user says "tomorrow", calculate tomorrow's date
   - Offer 3-4 relevant free slots
   - Once confirmed, call book_appointment with patient details (name and phone required)

4. **Clarification**: If you don't understand a request, politely ask for clarification.

5. **Clinic Info**: Share phone number, address, or other details as needed from the clinic data.

🕐 FLEXIBLE TIME BOOKING INSTRUCTIONS:
IMPORTANT: When a user requests a specific time (like "9:30 AM", "2:15 PM", etc.):

1. **Always check that exact time first** by calling available_slots with the requested date
2. **Look through the returned slots** to see if the requested time is available
3. **If the exact time is not in the list**, you can still book it IF:
   - There are no conflicts with existing appointments
   - The time falls within clinic working hours
   - The full duration can fit before the next appointment

4. **How to handle custom times**:
   - User says: "Can I get 9:30 AM?"
   - You call: available_slots(service="Braces", date="2025-07-21")
   - If 9:30 AM is not in the returned slots but 9:00 AM and 10:00 AM are free
   - You can say: "Let me check if 9:30 AM works for your 60-minute braces appointment"
   - Then call: available_slots again or explain availability

5. **Be flexible and helpful**:
   - If requested time isn't available, suggest the closest available times
   - Explain why a time might not work if there are conflicts
   - Always offer alternatives

6. **Example responses**:
   - "I can book you for 9:30 AM - the full 60-minute slot will be from 9:30 AM to 10:30 AM"
   - "9:30 AM isn't available due to another appointment, but I have 9:00 AM or 10:00 AM free"
   - "Let me check if 9:30 AM works for your appointment..."

🚦 BOOKING FLOW WITH CUSTOM TIMES:
1. User requests specific time
2. Call available_slots to check what's free
3. If exact time not listed but looks possible, be helpful and accommodating
4. Use your judgment about whether the time slot would work
5. Book using the exact time the user requested (if available)

📅 BOOKING FUNCTIONS:
- available_slots(service, date): Gets available slots for a service (automatically finds doctor)
- book_appointment(service, patient_name, slot, patient_phone): Books appointment (automatically finds doctor)

🚫 DO NOT:
- Provide medical advice
- Give details about procedures
- Invent information not found in the clinic data
- Change languages unexpectedly
- Use dates in the past (always use {today_date} or later)
- Ask which doctor for a service (the system finds the right doctor automatically)

🚫 OFF-TOPIC QUERIES:
If a user asks about something unrelated to the clinic, doctors, services, or appointments, respond with:
"I'm sorry, but I'm only able to assist you with information related to our services. For anything else, please feel free to contact us directly at:
📞 Phone: {clinic_phone}
We're here to help with any questions related to our clinic and services. 😊"

EXAMPLE BOOKING FLOW:
User: "I want to book [service] tomorrow"
Assistant: "I'll check available slots for [service] tomorrow. Let me see what's available."
[Call available_slots with service="[service]" and tomorrow's date]
[Show available slots with correct duration]
[Once user chooses, call book_appointment with the service and slot]

REMEMBER: 
- The system automatically handles doctor selection and service duration
- Always be helpful and professional
- Respond in the same language as the user's input
- Use the clinic data provided for all information
"""

def _build_service_mapping(clinic_data: dict) -> str:
    """
    Build a dynamic service mapping description from clinic data
    """
    if not clinic_data or 'Doctors' not in clinic_data:
        return "No service mapping available."
    
    mapping_lines = []
    
    for doctor in clinic_data.get('Doctors', []):
        doctor_name = doctor.get('Name', 'Unknown Doctor')
        speciality = doctor.get('Speciality', 'General')
        services = list(doctor.get('Services', {}).keys())
        
        if services:
            services_list = ", ".join(services)
            mapping_lines.append(f"- {speciality} services ({services_list}) → {doctor_name}")
    
    if not mapping_lines:
        return "No services configured."
    
    return "\n".join(mapping_lines)

def _build_duration_info(clinic_data: dict) -> str:
    """
    Build a dynamic duration information description from clinic data
    """
    if not clinic_data or 'Doctors' not in clinic_data:
        return "Duration information not available."
    
    duration_lines = []
    
    for doctor in clinic_data.get('Doctors', []):
        for service_name, duration_str in doctor.get('Services', {}).items():
            try:
                duration_minutes = int(duration_str.split()[0])
                duration_lines.append(f"- {service_name}: {duration_minutes} minutes")
            except:
                duration_lines.append(f"- {service_name}: {duration_str}")
    
    if not duration_lines:
        return "No duration information available."
    
    return "\n".join(duration_lines)

def _extract_available_services(clinic_data: dict) -> list:
    """
    Extract all available services from clinic data
    """
    services = []
    
    if clinic_data and 'Doctors' in clinic_data:
        for doctor in clinic_data['Doctors']:
            services.extend(list(doctor.get('Services', {}).keys()))
    
    return list(set(services))  # Remove duplicates

def _extract_doctor_names(clinic_data: dict) -> list:
    """
    Extract all doctor names from clinic data
    """
    doctors = []
    
    if clinic_data and 'Doctors' in clinic_data:
        for doctor in clinic_data['Doctors']:
            name = doctor.get('Name')
            if name:
                doctors.append(name)
    
    return doctors

def _extract_specialities(clinic_data: dict) -> list:
    """
    Extract all specialities from clinic data
    """
    specialities = []
    
    if clinic_data and 'Doctors' in clinic_data:
        for doctor in clinic_data['Doctors']:
            speciality = doctor.get('Speciality')
            if speciality:
                specialities.append(speciality)
    
    return list(set(specialities))  # Remove duplicates

def get_clinic_summary(clinic_data: dict) -> str:
    """
    Generate a summary of the clinic for debugging or information purposes
    """
    if not clinic_data:
        return "No clinic data available"
    
    clinic_name = clinic_data.get('clinic_name', 'Unknown Clinic')
    total_doctors = len(clinic_data.get('Doctors', []))
    all_services = _extract_available_services(clinic_data)
    all_specialities = _extract_specialities(clinic_data)
    
    summary = f"""
CLINIC SUMMARY
==============
Name: {clinic_name}
Address: {clinic_data.get('address', 'N/A')}
Phone: {clinic_data.get('phone', 'N/A')}
WhatsApp: {clinic_data.get('whatsapp_contact', 'N/A')}
Timezone: {clinic_data.get('timezone', 'N/A')}

Doctors: {total_doctors}
Specialities: {', '.join(all_specialities)}
Total Services: {len(all_services)}
Available Services: {', '.join(all_services)}
==============
    """.strip()
    
    return summary

def validate_clinic_data_structure(clinic_data: dict) -> dict:
    """
    Validate that clinic data has the expected structure
    """
    validation_result = {
        "valid": True,
        "errors": [],
        "warnings": []
    }
    
    # Check required fields
    if not isinstance(clinic_data, dict):
        validation_result["valid"] = False
        validation_result["errors"].append("Clinic data must be a dictionary")
        return validation_result
    
    # Check for doctors array
    if 'Doctors' not in clinic_data:
        validation_result["valid"] = False
        validation_result["errors"].append("Missing 'Doctors' field")
    elif not isinstance(clinic_data['Doctors'], list):
        validation_result["valid"] = False
        validation_result["errors"].append("'Doctors' must be a list")
    elif len(clinic_data['Doctors']) == 0:
        validation_result["warnings"].append("No doctors defined")
    
    # Check doctor structure
    if validation_result["valid"] and 'Doctors' in clinic_data:
        for i, doctor in enumerate(clinic_data['Doctors']):
            if not isinstance(doctor, dict):
                validation_result["errors"].append(f"Doctor {i} must be a dictionary")
                continue
            
            # Check required doctor fields
            required_fields = ['Name', 'Calendar_email', 'Services']
            for field in required_fields:
                if field not in doctor:
                    validation_result["warnings"].append(f"Doctor {i} missing '{field}' field")
            
            # Check services structure
            if 'Services' in doctor:
                if not isinstance(doctor['Services'], dict):
                    validation_result["warnings"].append(f"Doctor {i} Services must be a dictionary")
                elif len(doctor['Services']) == 0:
                    validation_result["warnings"].append(f"Doctor {i} has no services defined")
    
    # Check optional clinic fields
    optional_fields = ['clinic_name', 'address', 'phone', 'timezone']
    for field in optional_fields:
        if field not in clinic_data:
            validation_result["warnings"].append(f"Missing optional field '{field}'")
    
    if validation_result["errors"]:
        validation_result["valid"] = False
    
    return validation_result