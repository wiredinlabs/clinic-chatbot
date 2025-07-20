#!/usr/bin/env python3
"""
Multi-Clinic Chatbot Simulator
A command-line interface to test the chatbot API
"""

import requests
import json
import sys
from datetime import datetime
from typing import Dict, List, Optional

class ChatSimulator:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.selected_clinic = None
        self.user_phone = None
        self.user_name = None
        self.session_id = None
        self.user_id = None
        
    def print_header(self):
        """Print welcome header"""
        print("=" * 60)
        print("🏥 MULTI-CLINIC CHATBOT SIMULATOR")
        print("=" * 60)
        print()
    
    def check_health(self) -> bool:
        """Check if the API is running"""
        try:
            response = requests.get(f"{self.base_url}/api/v1/health/")
            if response.status_code == 200:
                health_data = response.json()
                print("✅ API Health Status:")
                print(f"   Status: {health_data.get('status', 'unknown')}")
                
                services = health_data.get('services', {})
                calendar_status = services.get('calendar', {})
                supabase_status = services.get('supabase', {})
                
                print(f"   📅 Calendar: {'✅ Connected' if calendar_status.get('service_initialized') else '❌ Disconnected'}")
                print(f"   🗄️  Database: {'✅ Connected' if supabase_status.get('connected') else '❌ Disconnected'}")
                print()
                return True
            else:
                print(f"❌ Health check failed: {response.status_code}")
                return False
        except requests.exceptions.ConnectionError:
            print(f"❌ Cannot connect to API at {self.base_url}")
            print("   Make sure the FastAPI server is running:")
            print("   python main.py")
            return False
        except Exception as e:
            print(f"❌ Health check error: {e}")
            return False
    
    def get_clinics(self) -> List[Dict]:
        """Fetch available clinics"""
        try:
            response = requests.get(f"{self.base_url}/api/v1/clinics/")
            if response.status_code == 200:
                return response.json()
            else:
                print(f"❌ Failed to fetch clinics: {response.status_code}")
                return []
        except Exception as e:
            print(f"❌ Error fetching clinics: {e}")
            return []
    
    def display_clinics(self, clinics: List[Dict]) -> None:
        """Display available clinics"""
        print("🏥 AVAILABLE CLINICS:")
        print("-" * 40)
        for i, clinic in enumerate(clinics, 1):
            print(f"{i}. {clinic['clinic_name']}")
            print(f"   ID: {clinic['clinic_id']}")
            print(f"   📍 {clinic.get('address', 'N/A')}")
            print(f"   📞 {clinic.get('phone', 'N/A')}")
            print()
    
    def select_clinic(self, clinics: List[Dict]) -> Optional[Dict]:
        """Let user select a clinic"""
        while True:
            try:
                choice = input(f"Select clinic (1-{len(clinics)}) or 'q' to quit: ").strip()
                
                if choice.lower() == 'q':
                    return None
                
                choice_num = int(choice)
                if 1 <= choice_num <= len(clinics):
                    selected = clinics[choice_num - 1]
                    print(f"\n✅ Selected: {selected['clinic_name']}")
                    return selected
                else:
                    print(f"❌ Please enter a number between 1 and {len(clinics)}")
            except ValueError:
                print("❌ Please enter a valid number or 'q' to quit")
    
    def get_user_info(self) -> bool:
        """Get user information"""
        print("\n👤 USER INFORMATION:")
        print("-" * 20)
        
        while True:
            phone = input("Enter your phone number (e.g., +923001234567): ").strip()
            if phone:
                self.user_phone = phone
                break
            print("❌ Phone number is required")
        
        name = input("Enter your name (optional): ").strip()
        self.user_name = name if name else "Test User"
        
        print(f"\n✅ User: {self.user_name} ({self.user_phone})")
        return True
    
    def get_clinic_services(self, clinic_id: str) -> None:
        """Display clinic services"""
        try:
            response = requests.get(f"{self.base_url}/api/v1/clinics/{clinic_id}/services")
            if response.status_code == 200:
                data = response.json()
                services = data.get('services', {})
                clinic_info = data.get('clinic_info', {})
                
                print(f"\n🩺 SERVICES AT {clinic_info.get('name', 'This Clinic')}:")
                print("-" * 50)
                
                for service, details in services.items():
                    doctor_name = details.get('doctor_name', 'Unknown')
                    speciality = details.get('speciality', 'General')
                    duration = details.get('duration_display', 'Unknown duration')
                    
                    print(f"• {service}")
                    print(f"  👨‍⚕️ Dr. {doctor_name} ({speciality})")
                    print(f"  ⏱️  Duration: {duration}")
                    print()
                
                print("💬 You can ask about any of these services or book appointments!")
                print()
        except Exception as e:
            print(f"❌ Error fetching services: {e}")
    
    def send_message(self, message: str) -> Optional[Dict]:
        """Send message to chatbot"""
        payload = {
            "message": message,
            "clinic_id": self.selected_clinic['clinic_id'],
            "phone_number": self.user_phone,
            "user_name": self.user_name
        }
        
        try:
            print("🤖 Thinking...")
            response = requests.post(
                f"{self.base_url}/api/v1/chat",
                json=payload,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Store session info
                if not self.session_id:
                    self.session_id = data.get('session_id')
                    self.user_id = data.get('user_id')
                
                return data
            else:
                print(f"❌ API Error {response.status_code}: {response.text}")
                return None
                
        except Exception as e:
            print(f"❌ Error sending message: {e}")
            return None
    
    def display_response(self, response_data: Dict) -> None:
        """Display bot response"""
        bot_response = response_data.get('response', 'No response received')
        clinic_name = response_data.get('clinic_name', 'Clinic')
        
        print(f"\n🤖 {clinic_name} Bot:")
        print("-" * 30)
        print(bot_response)
        print()
    
    def show_chat_commands(self) -> None:
        """Show available commands"""
        print("💡 CHAT COMMANDS:")
        print("-" * 20)
        print("• Type your message and press Enter")
        print("• '/history' - View chat history")
        print("• '/appointments' - View your appointments")
        print("• '/services' - Show clinic services")
        print("• '/clear' - Clear chat history")
        print("• '/switch' - Switch to different clinic")
        print("• '/quit' or 'q' - Exit simulator")
        print()
    
    def get_chat_history(self) -> None:
        """Get and display chat history"""
        try:
            url = f"{self.base_url}/api/v1/users/{self.user_phone}/history"
            params = {"clinic_id": self.selected_clinic['clinic_id']}
            
            response = requests.get(url, params=params)
            if response.status_code == 200:
                data = response.json()
                messages = data.get('messages', [])
                
                print("\n📝 CHAT HISTORY:")
                print("-" * 30)
                
                if not messages:
                    print("No chat history found.")
                else:
                    for msg in messages[-10:]:  # Show last 10 messages
                        role = msg.get('role', 'unknown')
                        content = msg.get('content', '')
                        
                        if role == 'user':
                            print(f"👤 You: {content}")
                        elif role == 'assistant':
                            print(f"🤖 Bot: {content}")
                        elif role == 'tool':
                            print(f"🔧 System: {content}")
                        print()
            else:
                print(f"❌ Failed to get history: {response.status_code}")
        except Exception as e:
            print(f"❌ Error getting history: {e}")
    
    def get_appointments(self) -> None:
        """Get and display user appointments"""
        try:
            url = f"{self.base_url}/api/v1/users/{self.user_phone}/appointments"
            params = {"clinic_id": self.selected_clinic['clinic_id']}
            
            response = requests.get(url, params=params)
            if response.status_code == 200:
                data = response.json()
                appointments = data.get('appointments', [])
                
                print("\n📅 YOUR APPOINTMENTS:")
                print("-" * 30)
                
                if not appointments:
                    print("No appointments found.")
                else:
                    for apt in appointments:
                        service = apt.get('service', 'Unknown')
                        datetime_str = apt.get('appointment_datetime', '')
                        status = apt.get('status', 'unknown')
                        doctor_name = apt.get('doctors', {}).get('name', 'Unknown') if apt.get('doctors') else 'Unknown'
                        
                        # Format datetime
                        if datetime_str:
                            try:
                                dt = datetime.fromisoformat(datetime_str.replace('Z', '+00:00'))
                                formatted_time = dt.strftime('%Y-%m-%d %I:%M %p')
                            except:
                                formatted_time = datetime_str
                        else:
                            formatted_time = 'Unknown time'
                        
                        print(f"• {service}")
                        print(f"  📅 {formatted_time}")
                        print(f"  👨‍⚕️ Dr. {doctor_name}")
                        print(f"  📋 Status: {status}")
                        print()
            else:
                print(f"❌ Failed to get appointments: {response.status_code}")
        except Exception as e:
            print(f"❌ Error getting appointments: {e}")
    
    def clear_history(self) -> None:
        """Clear chat history"""
        try:
            url = f"{self.base_url}/api/v1/users/{self.user_phone}/history"
            params = {"clinic_id": self.selected_clinic['clinic_id']}
            
            confirm = input("Are you sure you want to clear your chat history? (yes/no): ").strip().lower()
            if confirm in ['yes', 'y']:
                response = requests.delete(url, params=params)
                if response.status_code == 200:
                    print("✅ Chat history cleared successfully!")
                    self.session_id = None
                    self.user_id = None
                else:
                    print(f"❌ Failed to clear history: {response.status_code}")
            else:
                print("❌ History clearing cancelled.")
        except Exception as e:
            print(f"❌ Error clearing history: {e}")
    
    def chat_loop(self) -> None:
        """Main chat interaction loop"""
        print(f"\n💬 CHATTING WITH {self.selected_clinic['clinic_name']}")
        print("=" * 50)
        
        # Show available services
        self.get_clinic_services(self.selected_clinic['clinic_id'])
        
        # Show commands
        self.show_chat_commands()
        
        while True:
            try:
                # Get user input
                user_input = input(f"👤 {self.user_name}: ").strip()
                
                if not user_input:
                    continue
                
                # Handle commands
                if user_input.lower() in ['/quit', 'q']:
                    print("👋 Goodbye!")
                    break
                elif user_input.lower() == '/history':
                    self.get_chat_history()
                    continue
                elif user_input.lower() == '/appointments':
                    self.get_appointments()
                    continue
                elif user_input.lower() == '/services':
                    self.get_clinic_services(self.selected_clinic['clinic_id'])
                    continue
                elif user_input.lower() == '/clear':
                    self.clear_history()
                    continue
                elif user_input.lower() == '/switch':
                    print("👋 Switching clinics...")
                    break
                elif user_input.lower() == '/help':
                    self.show_chat_commands()
                    continue
                
                # Send message to bot
                response_data = self.send_message(user_input)
                
                if response_data:
                    self.display_response(response_data)
                else:
                    print("❌ Failed to get response from bot")
                    
            except KeyboardInterrupt:
                print("\n\n👋 Chat interrupted. Goodbye!")
                break
            except Exception as e:
                print(f"❌ Chat error: {e}")
    
    def run(self) -> None:
        """Main simulator loop"""
        self.print_header()
        
        # Check API health
        if not self.check_health():
            return
        
        while True:
            # Get clinics
            clinics = self.get_clinics()
            if not clinics:
                print("❌ No clinics available. Make sure your database is set up.")
                return
            
            # Display and select clinic
            self.display_clinics(clinics)
            selected_clinic = self.select_clinic(clinics)
            
            if not selected_clinic:
                print("👋 Goodbye!")
                break
            
            self.selected_clinic = selected_clinic
            
            # Get user info
            if not self.get_user_info():
                continue
            
            # Start chat
            self.chat_loop()
            
            # Ask if user wants to continue with another clinic
            continue_choice = input("\nWould you like to chat with another clinic? (y/n): ").strip().lower()
            if continue_choice not in ['y', 'yes']:
                print("👋 Thank you for using the clinic chatbot!")
                break

def main():
    """Entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Multi-Clinic Chatbot Simulator")
    parser.add_argument(
        "--url", 
        default="http://localhost:8000",
        help="Base URL of the FastAPI server (default: http://localhost:8000)"
    )
    
    args = parser.parse_args()
    
    simulator = ChatSimulator(base_url=args.url)
    simulator.run()

if __name__ == "__main__":
    main()