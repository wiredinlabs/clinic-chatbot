from fastapi import APIRouter, HTTPException
from typing import Dict, Any
import json
import asyncio
from datetime import datetime, timedelta

from app.models.chat_models import ChatRequest, ChatResponse
from app.services.supabase_service import supabase_service
from app.services.openai_service import openai_service
from app.utils.prompt import get_system_prompt
from app.utils.functions import available_slots, book_appointment

router = APIRouter(tags=["chat"])

@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    """
    Main chat endpoint for multi-clinic chatbot
    """
    user_input = request.message.strip()
    clinic_id = request.clinic_id
    phone_number = request.phone_number
    user_name = request.user_name
    
    # Handle empty messages
    if not user_input:
        return ChatResponse(
            response="I'm here to help you. Please let me know what you need assistance with.",
            session_id="",
            user_id="",
            clinic_name=""
        )
    
    try:
        # 1. Get clinic data from Supabase
        clinic_data = await supabase_service.get_clinic_data(clinic_id)
        if not clinic_data:
            raise HTTPException(status_code=404, detail=f"Clinic not found: {clinic_id}")
        
        # 2. Get or create user
        user = await supabase_service.get_or_create_user(phone_number, clinic_id, user_name)
        if not user:
            raise HTTPException(status_code=500, detail="Failed to manage user")
        
        # 3. Get or create chat session
        session = await supabase_service.get_chat_session(user['id'], clinic_id)
        if not session:
            raise HTTPException(status_code=500, detail="Failed to manage chat session")
        
        # 4. Load chat history
        chat_history = await supabase_service.get_chat_history(session['id'])
        
        # 5. Add current user message to history and save it
        chat_history.append({"role": "user", "content": user_input})
        await supabase_service.save_message(
            session['id'], user['id'], clinic_id, 
            "user", user_input
        )
        
        # 6. Generate system prompt with clinic data
        system_prompt = get_system_prompt(clinic_data)
        
        # 7. Get response from OpenAI
        response = openai_service.call_openai(chat_history, system_prompt)
        reply = response.choices[0].message

        # 8. Handle tool calls
        if reply.tool_calls:
            # Add the assistant's tool call message to history and save it
            tool_calls_data = [
                {
                    "id": tool_call.id,
                    "type": "function",
                    "function": {
                        "name": tool_call.function.name,
                        "arguments": tool_call.function.arguments
                    }
                } for tool_call in reply.tool_calls
            ]
            
            chat_history.append({
                "role": "assistant", 
                "content": reply.content,
                "tool_calls": tool_calls_data
            })
            
            await supabase_service.save_message(
                session['id'], user['id'], clinic_id,
                "assistant", reply.content, tool_calls_data
            )
            
            # Process each tool call
            for tool_call in reply.tool_calls:
                fn_name = tool_call.function.name
                args = json.loads(tool_call.function.arguments)

                # Handle date conversions for available_slots
                if fn_name == "available_slots" and "date" in args:
                    args = _process_date_argument(args)

                # Execute the function
                try:
                    if fn_name == "available_slots":
                        print(f"🔍 Getting slots for service: {args['service']} on {args['date']}")
                        result = await available_slots(
                            service=args["service"],
                            date=args["date"],
                            clinic_data=clinic_data
                        )
                        
                    elif fn_name == "book_appointment":
                        print(f"📅 Booking appointment for service: {args['service']}")
                        result = await book_appointment(
                            service=args["service"],
                            patient_name=args["patient_name"],
                            slot=args["slot"],
                            patient_phone=args.get("patient_phone", phone_number),
                            clinic_data=clinic_data
                        )
                        
                        # If booking was successful, save appointment to database
                        if isinstance(result, str) and "✅ Appointment Confirmed!" in result:
                            appointment_details = {
                                'patient_name': args["patient_name"],
                                'patient_phone': args.get("patient_phone", phone_number),
                                'service': args["service"],
                                'appointment_time_utc': args["slot"],
                                'duration_minutes': 30,  # Default, should be extracted from clinic data
                                'doctor_email': None,  # Should be extracted from clinic data
                                'event_id': None,
                                'event_link': None
                            }
                            
                            await supabase_service.save_appointment(
                                user['id'], clinic_id, appointment_details
                            )
                        
                    else:
                        result = "Unknown function"
                        
                except Exception as e:
                    print(f"❌ Error executing {fn_name}: {e}")
                    result = f"Error executing function: {str(e)}"

                # Add function result to chat history and save it
                tool_result_content = json.dumps(result) if isinstance(result, (list, dict)) else str(result)
                
                chat_history.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "name": fn_name,
                    "content": tool_result_content
                })
                
                await supabase_service.save_message(
                    session['id'], user['id'], clinic_id,
                    "tool", tool_result_content, 
                    tool_call_id=tool_call.id, function_name=fn_name
                )

            # Get final response from OpenAI after function execution
            response = openai_service.call_openai(chat_history, system_prompt)
            reply = response.choices[0].message

        # 9. Add final assistant response to history and save it
        chat_history.append({"role": "assistant", "content": reply.content})
        await supabase_service.save_message(
            session['id'], user['id'], clinic_id,
            "assistant", reply.content
        )
        
        # 10. Update session data as backup
        await supabase_service.update_session_data(session['id'], chat_history)
        
        return ChatResponse(
            response=reply.content,
            session_id=session['id'],
            user_id=user['id'],
            clinic_name=clinic_data.get('clinic_name', '')
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Unexpected error in chat endpoint: {e}")
        return ChatResponse(
            response="I'm sorry, there was an error processing your request. Please try again or contact our support team.",
            session_id="",
            user_id="",
            clinic_name="",
            error=str(e)
        )

def _process_date_argument(args: Dict[str, Any]) -> Dict[str, Any]:
    """Process and validate date arguments for tool calls"""
    date_str = args["date"].lower().strip()
    
    # Handle relative dates
    if date_str == "today":
        args["date"] = datetime.now().strftime("%Y-%m-%d")
        print(f"🔄 Converted 'today' to: {args['date']}")
    elif date_str == "tomorrow":
        tomorrow = datetime.now() + timedelta(days=1)
        args["date"] = tomorrow.strftime("%Y-%m-%d")
        print(f"🔄 Converted 'tomorrow' to: {args['date']}")
    else:
        # Check if the date is valid and not in the past
        try:
            parsed_date = datetime.strptime(args["date"], "%Y-%m-%d")
            today = datetime.now()
            
            # If the date is more than 1 year in the past, use today
            if parsed_date < today - timedelta(days=365):
                print(f"⚠️ Detected old date {args['date']}, using today instead")
                args["date"] = today.strftime("%Y-%m-%d")
            # If date is in the past (but recent), use today
            elif parsed_date.date() < today.date():
                print(f"⚠️ Date {args['date']} is in the past, using today instead")
                args["date"] = today.strftime("%Y-%m-%d")
            else:
                print(f"✅ Using date: {args['date']}")
        except ValueError:
            # If date parsing fails, use today
            print(f"❌ Invalid date format {args['date']}, using today")
            args["date"] = datetime.now().strftime("%Y-%m-%d")
    
    return args