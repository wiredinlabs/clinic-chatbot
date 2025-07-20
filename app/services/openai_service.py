from openai import OpenAI
from typing import List, Dict, Any
from app.config.settings import settings

class OpenAIService:
    def __init__(self):
        self.client = OpenAI(api_key=settings.openai_api_key)
        self.tools = [
            {
                "type": "function",
                "function": {
                    "name": "available_slots",
                    "description": "Get available appointment slots for a specific service (automatically finds the right doctor)",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "service": {
                                "type": "string",
                                "description": "The specific service/treatment requested (e.g., 'Hydrafacial', 'Braces', 'Botox')"
                            },
                            "date": {
                                "type": "string", 
                                "format": "date",
                                "description": "Date in YYYY-MM-DD format"
                            }
                        },
                        "required": ["service", "date"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "book_appointment",
                    "description": "Book a confirmed appointment for a patient (automatically finds the right doctor for the service)",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "service": {
                                "type": "string",
                                "description": "The specific service/treatment being booked"
                            },
                            "patient_name": {
                                "type": "string",
                                "description": "Full name of the patient"
                            },
                            "slot": {
                                "type": "string",
                                "description": "The selected time slot in format 'YYYY-MM-DD HH:MM AM/PM'"
                            },
                            "patient_phone": {
                                "type": "string", 
                                "description": "Patient's phone number (optional but recommended)"
                            }
                        },
                        "required": ["service", "patient_name", "slot"]
                    }
                }
            }
        ]

    def call_openai(self, chat_history: List[Dict[str, Any]], system_prompt: str):
        """
        Call OpenAI API with chat history and system prompt
        """
        messages = [{"role": "system", "content": system_prompt}]

        # Track whether the last message was a tool_call
        expecting_tool_response = False

        for msg in chat_history:
            if msg["role"] == "assistant" and "tool_calls" in msg:
                messages.append(msg)
                expecting_tool_response = True
            elif msg["role"] == "tool":
                if expecting_tool_response:
                    messages.append(msg)
                    expecting_tool_response = False  # Reset after valid tool response
                else:
                    print("⚠️ Skipping orphan tool message:", msg)
            else:
                messages.append(msg)
                expecting_tool_response = False  # Reset for normal messages

        try:
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=messages,
                tools=self.tools,
                tool_choice="auto",
                temperature=0.1,  # Lower temperature for more consistent responses
                max_tokens=1000   # Reasonable limit for chat responses
            )
            return response
        except Exception as e:
            print(f"❌ OpenAI call failed: {e}")
            raise

    def call_openai_simple(self, message: str, system_prompt: str = None):
        """
        Simple OpenAI call for single message (useful for utilities)
        """
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": message})

        try:
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=messages,
                temperature=0.1,
                max_tokens=500
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"❌ Simple OpenAI call failed: {e}")
            raise

# Create global instance
openai_service = OpenAIService()