# Multi-Clinic Chatbot Backend

An AI-powered chatbot system built with FastAPI that provides intelligent appointment booking and patient communication for multiple medical clinics.

## 🌟 Features

- **Multi-Clinic Support**: Manage multiple clinics from a single backend
- **AI-Powered Conversations**: GPT-4 integration for natural language understanding
- **Real Appointment Booking**: Google Calendar integration for actual appointment scheduling
- **Multi-Language Support**: English and Roman Urdu conversation support
- **Automatic Doctor Selection**: Smart matching of services to appropriate doctors
- **Persistent Chat History**: Complete conversation tracking and session management
- **RESTful API**: Comprehensive REST API with interactive documentation

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   FastAPI       │    │   Supabase      │
│   (Chat UI)     │◄──►│   Backend       │◄──►│   Database      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                               │
                               ▼
                       ┌─────────────────┐    ┌─────────────────┐
                       │   OpenAI        │    │   Google        │
                       │   GPT-4         │    │   Calendar      │
                       └─────────────────┘    └─────────────────┘
```

## 🚀 Quick Start

### Prerequisites

- Python 3.9+
- OpenAI API key
- Supabase account
- Google Cloud account (optional, for calendar integration)

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd clinic-chatbot-backend
   ```

2. **Set up virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install fastapi uvicorn openai supabase python-dotenv pydantic
   pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client
   ```

4. **Configure environment**
   
   Create `.env` file:
   ```bash
   OPENAI_API_KEY=your_openai_key_here
   SUPABASE_URL=your_supabase_url
   SUPABASE_ANON_KEY=your_supabase_anon_key
   GOOGLE_CALENDAR_CREDENTIALS_FILE=credentials/google-credentials.json
   DEFAULT_TIMEZONE=Asia/Karachi
   ```

5. **Set up database**
   
   Create Supabase tables (see [Testing Guide](./TESTING_GUIDE.md) for SQL scripts)

6. **Start the server**
   ```bash
   python main.py
   ```

Visit `http://localhost:8000/docs` for API documentation.

## 📡 API Endpoints

### Chat
- `POST /api/v1/chat` - Main conversation endpoint

### Clinics
- `GET /api/v1/clinics/` - List all clinics
- `GET /api/v1/clinics/{clinic_id}/services` - Get clinic services
- `POST /api/v1/clinics/` - Create new clinic

### Users
- `GET /api/v1/users/{phone}/history` - Get chat history
- `GET /api/v1/users/{phone}/appointments` - Get appointments
- `DELETE /api/v1/users/{phone}/history` - Clear chat history

### Health
- `GET /api/v1/health/` - System status
- `GET /api/v1/health/calendar` - Calendar service status

## 💬 Usage Examples

### Basic Chat
```bash
curl -X POST "http://localhost:8000/api/v1/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "I want to book a hydrafacial appointment",
    "clinic_id": "skin_and_smile_clinic_lahore",
    "phone_number": "+923001234567",
    "user_name": "John Doe"
  }'
```

### Service Inquiry
```bash
curl -X POST "http://localhost:8000/api/v1/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What services do you offer?",
    "clinic_id": "skin_and_smile_clinic_lahore",
    "phone_number": "+923001234567"
  }'
```

## 🧠 AI Capabilities

The system uses OpenAI's function calling to handle:

- **Service Recognition**: Understands patient requests for medical services
- **Appointment Scheduling**: Automatically finds available slots and books appointments
- **Doctor Matching**: Selects appropriate doctors based on requested services
- **Multi-Language Support**: Responds in English or Roman Urdu based on input

### Supported Functions

1. **available_slots**: Get available appointment times for a service
2. **book_appointment**: Confirm and schedule patient appointments

## 🏥 Multi-Clinic Setup

Each clinic requires:

```json
{
  "clinic_id": "unique_clinic_identifier",
  "clinic_name": "Clinic Display Name",
  "address": "Full clinic address",
  "phone": "Contact number",
  "timezone": "Asia/Karachi",
  "doctors": [
    {
      "name": "Dr. Name",
      "speciality": "Medical Speciality",
      "calendar_email": "doctor@gmail.com",
      "services": {
        "Service Name": "Duration in minutes"
      }
    }
  ]
}
```

## 📊 Database Schema

- **clinics**: Clinic information and configuration
- **doctors**: Doctor profiles with services and calendar integration
- **users**: Patient contact information
- **chat_sessions**: Conversation session management
- **chat_messages**: Individual message storage
- **appointments**: Booking records and confirmations

## 🔧 Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `OPENAI_API_KEY` | OpenAI API key | Required |
| `SUPABASE_URL` | Supabase project URL | Required |
| `SUPABASE_ANON_KEY` | Supabase anonymous key | Required |
| `DEFAULT_TIMEZONE` | Clinic timezone | `Asia/Karachi` |
| `DEFAULT_START_HOUR` | Clinic opening hour | `9` |
| `DEFAULT_END_HOUR` | Clinic closing hour | `19` |
| `SESSION_TIMEOUT_HOURS` | Chat session timeout | `24` |

### Clinic Hours Configuration

```json
{
  "config": {
    "working_hours": {
      "start": "09:00",
      "end": "18:00"
    }
  }
}
```

## 🔒 Security

- **Environment-based configuration**: Secure secret management
- **Input validation**: Pydantic model validation
- **CORS configuration**: Cross-origin request handling
- **API key protection**: Secure external service authentication

## 📈 Monitoring

Health check endpoints provide:
- **System status**: Overall application health
- **Calendar status**: Google Calendar connectivity
- **Database status**: Supabase connection health

## 🧪 Testing

See [Testing Guide](./TESTING_GUIDE.md) for detailed testing instructions.

Quick test:
```bash
# Health check
curl http://localhost:8000/api/v1/health/

# Basic chat test
curl -X POST "http://localhost:8000/api/v1/chat" \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello", "clinic_id": "test_clinic", "phone_number": "+1234567890"}'
```

## 📚 Documentation

- [Architecture Document](./ARCHITECTURE.md) - Detailed system architecture
- [Testing Guide](./TESTING_GUIDE.md) - Setup and testing instructions
- [API Documentation](http://localhost:8000/docs) - Interactive API docs (when running)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/new-feature`)
3. Commit changes (`git commit -am 'Add new feature'`)
4. Push to branch (`git push origin feature/new-feature`)
5. Create Pull Request

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

- **Documentation**: Check the guides in the docs folder
- **Issues**: Create GitHub issues for bugs or feature requests
- **Health Check**: Use `/api/v1/health/` endpoint for system status

## 🚀 Deployment

### Local Development
```bash
python main.py
```

### Production
```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

### Docker (Optional)
```dockerfile
FROM python:3.9
COPY . /app
WORKDIR /app
RUN pip install -r requirements.txt
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

---

**Built with ❤️ using FastAPI, OpenAI GPT-4, and Supabase**