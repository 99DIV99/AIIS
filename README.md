<div align="center">

# 🚀 AIIS Backend

### *AI-Powered Team Collaboration & Daily Synthesis*

[![Python](https://img.shields.io/badge/Python-3.11%2B-blue)](https://www.python.org/)
[![Django](https://img.shields.io/badge/Django-5.2-green)](https://www.djangoproject.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

*A Django REST API that powers team status updates, real-time collaboration, and AI-generated daily summaries.*

</div>

---

## ✨ Features

### 📝 Team Status Updates
- **Tweet-style updates** - Team members log what they're working on
- **Role-aware** - Backend Dev, Frontend Dev, Product Manager, UI/UX Designer
- **Feed-based** - See recent activity from the entire team

### 🤖 AI-Powered Daily Summaries
- **Multi-LLM Architecture** - Gemini (primary) → Groq → OpenRouter fallback
- **Personal Briefs** - Individual daily summaries with achievements, blockers, and vibes
- **Team Hub** - Office-wide synthesis of everyone's progress
- **Auto-generated** - One click generates all summaries for the day

### 🔄 Real-Time Features
- **WebSocket Live Status** - See who's online and what they're working on
- **Team Pings** - Quick questions like "Coffee?" with yes/no responses
- **Instant Updates** - Status changes propagate immediately

### 🔐 Authentication & Security
- **JWT Tokens** - Secure authentication with SimpleJWT
- **Role-Based Profiles** - User profiles with customizable roles
- **CORS Configured** - Ready for frontend integration

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                         Frontend (Next.js)                   │
│                         :4000 (dev)                          │
└──────────────────────────────┬──────────────────────────────┘
                               │ HTTP + WebSocket
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                      Django REST Framework                   │
│                         :8000 (dev)                          │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌──────────────┐  ┌─────────────────┐   │
│  │   Views     │  │  Consumers   │  │     Tasks       │   │
│  │  (REST API) │  │ (WebSocket)  │  │   (Celery)      │   │
│  └─────────────┘  └──────────────┘  └─────────────────┘   │
└──────────────────────────────┬──────────────────────────────┘
                               │
        ┌──────────────────────┼──────────────────────┐
        ▼                      ▼                      ▼
┌───────────────┐    ┌─────────────────┐    ┌───────────────┐
│  PostgreSQL   │    │      Redis      │    │  AI Services  │
│  (aiis_db)    │    │  (Celery + WS)  │    │  Gemini/Groq  │
└───────────────┘    └─────────────────┘    └───────────────┘
```

---

## 🛠️ Tech Stack

| Component | Technology |
|-----------|------------|
| **Framework** | Django 5.2 |
| **API** | Django REST Framework |
| **Auth** | SimpleJWT |
| **Async** | Celery + django-celery-beat |
| **Real-time** | Django Channels (WebSockets) |
| **Database** | PostgreSQL |
| **Cache/Broker** | Redis |
| **AI Services** | Gemini, Groq, OpenRouter |

---

## 📦 Requirements

```bash
# Core Django
Django>=5.2
djangorestframework
djangorestframework-simplejwt

# Async & Real-time
celery
django-celery-beat
channels
channels-redis
daphne

# CORS
django-cors-headers

# AI SDKs
google-genai
groq

# Database
psycopg2-binary

# Environment
python-dotenv
```

---

## 🚀 Quick Start

### 1. Clone & Setup

```bash
git clone https://github.com/yourusername/aiis-daily.git
cd aiis-daily

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Environment Variables

Create a `.env` file:

```bash
# Django
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Database
DB_NAME=aiis_db
DB_USER=aiis_user
DB_PASSWORD=aiis_pass
DB_HOST=localhost
DB_PORT=5432

# Redis
REDIS_URL=redis://localhost:6379/0

# AI Services (at least one required)
GEMINI_API_KEY=your-gemini-key
GROQ_API_KEY=your-groq-key
OPENROUTER_API_KEY=your-openrouter-key
```

### 3. Database Setup

```bash
# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Run server
python manage.py runserver
```

### 4. Start Celery (for AI summaries)

```bash
# Terminal 1: Redis
redis-server

# Terminal 2: Celery worker
celery -A aiis_backend worker -l info

# Terminal 3: Celery beat (scheduler)
celery -A aiis_backend beat -l info
```

---

## 📡 API Endpoints

### Authentication
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/auth/register/` | POST | Create new user |
| `/api/auth/login/` | POST | Get JWT tokens |
| `/api/auth/refresh/` | POST | Refresh access token |
| `/api/me/` | GET | Get current user profile |

### Status Updates
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/tweets/` | GET | List all status updates |
| `/api/tweets/` | POST | Create new status update |

### Team Features
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/team-ping/` | POST | Send team ping question |
| `/api/team-ping/<id>/reply/` | POST | Reply yes/no to ping |
| `/api/team-status/` | WS | Live team status channel |

### AI Summaries
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/summary/generate/` | POST | Generate daily summaries |
| `/api/v1/summary/individual/` | GET | Get personal summaries |
| `/api/v1/summary/team/` | GET | Get team summaries |

---

## 🔧 Configuration

### CORS Settings

Edit `settings.py` to add your frontend domain:

```python
CORS_ALLOWED_ORIGINS = [
    "http://localhost:4000",  # Next.js dev
    "https://yourdomain.com",  # Production
]
```

### WebSocket Connection

```javascript
// Frontend WebSocket connection
const ws = new WebSocket('ws://localhost:8000/ws/team-status/');
ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    console.log('Live update:', data);
};
```

---

## 🤖 AI Integration

### Multi-LLM Fallback Strategy

The system tries AI providers in order:

1. **Gemini** (`gemini-2.0-flash` or `gemini-1.5-flash`)
2. **Groq** (`llama3-70b-8192`) 
3. **OpenRouter** (`deepseek/deepseek-r1-0528:free`)

### Summary Prompt Template

Personal summaries include:
- 🚀 Tasks Completed
- 🚧 Work in Progress
- 🛑 Blockers
- 🌟 The Vibe

Team summaries include:
- 🏆 Today's Core Achievements
- 🤝 Team Bottlenecks
- ☕ The Watercooler
- 👥 Member Highlights

---

## 📁 Project Structure

```
backend/
├── aiis_backend/          # Project configuration
│   ├── settings.py        # Django settings
│   ├── urls.py           # Root URL config
│   ├── asgi.py           # ASGI (WebSocket) config
│   ├── celery.py         # Celery configuration
│   └── wsgi.py           # WSGI config
├── core/                 # Main app
│   ├── models.py         # User, Tweet, Summary models
│   ├── views.py          # API views
│   ├── consumers.py      # WebSocket consumers
│   ├── serializers.py    # DRF serializers
│   ├── utils.py          # AI integration
│   ├── tasks.py          # Celery tasks
│   └── urls.py           # App URLs
├── manage.py
├── .gitignore
├── .env                  # Environment variables (not tracked)
└── README.md
```

---

## 🧪 Development

### Run Tests

```bash
python manage.py test
```

### Database Shell

```bash
python manage.py dbshell
```

### Create Migrations

```bash
python manage.py makemigrations
python manage.py migrate
```

---

## 📝 License

MIT License - feel free to use this for your projects!

---

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## 📧 Support

For questions or issues, please open a GitHub issue.

---

<div align="center">

**Built with ❤️ for productive teams**

</div>
