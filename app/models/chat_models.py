# app/models/chat_models.py
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class ChatRequest(BaseModel):
    message: str = Field(..., description="The user's message")
    clinic_id: str = Field(..., description="Unique identifier for the clinic")
    phone_number: str = Field(..., description="User's phone number")
    user_name: Optional[str] = Field(None, description="User's name (optional)")

    class Config:
        schema_extra = {
            "example": {
                "message": "I want to book an appointment for hydrafacial",
                "clinic_id": "skin_and_smile_clinic_lahore",
                "phone_number": "+923001234567",
                "user_name": "John Doe"
            }
        }

class ChatResponse(BaseModel):
    response: str = Field(..., description="The assistant's response")
    session_id: str = Field(..., description="Chat session identifier")
    user_id: str = Field(..., description="User identifier")
    clinic_name: str = Field(..., description="Name of the clinic")
    error: Optional[str] = Field(None, description="Error message if any")

class ChatMessage(BaseModel):
    role: str = Field(..., description="Message role: user, assistant, or tool")
    content: str = Field(..., description="Message content")
    tool_calls: Optional[List[Dict[str, Any]]] = Field(None, description="Tool calls if any")
    tool_call_id: Optional[str] = Field(None, description="Tool call ID for tool responses")
    name: Optional[str] = Field(None, description="Function name for tool messages")