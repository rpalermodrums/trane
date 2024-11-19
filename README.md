# Transcribe - Audio Source Separation Tool

## Overview

Transcribe is a full-stack application that provides audio source separation capabilities using the Demucs model. It offers both a web interface and a CLI tool for processing audio files.

## Features

- Audio source separation using multiple Demucs models
- Real-time progress tracking
- Advanced audio player with track management
- CLI interface for batch processing
- User authentication and task management
- WebSocket-based progress updates

## Architecture

### Backend (Django + Celery)

- Django REST framework for API endpoints
- Celery for asynchronous task processing
- Channels for WebSocket communication
- PostgreSQL for data storage
- Redis for task queue and WebSocket backend

### Frontend (React + TypeScript)

- React with TypeScript for type safety
- TanStack Query for data fetching
- WebSocket integration for real-time updates
- Tailwind CSS for styling
- Shadcn UI components

## Installation

### Prerequisites

- Docker and Docker Compose
- Node.js 18+ (for local development)
- Python 3.12+ (for local development)

### Quick Start

1. Clone the repository:
I'll help you complete the README.md. Here's the continuation from where it left off:

```markdown
### Quick Start
1. Clone the repository:
```bash
git clone https://github.com/yourusername/transcribe.git
cd transcribe
```

1. Create a .env file in the root directory:

```bash
DEBUG=1
DJANGO_SECRET_KEY=your-secret-key
POSTGRES_DB=database
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
REDIS_HOST=redis
REDIS_PORT=6379
```

1. Build and start the containers:

```bash
docker compose up -d --build
```

1. Create a superuser for Django admin:

```bash
docker compose exec backend python manage.py createsuperuser
```

1. Access the application:

- Frontend: <http://localhost>
- Backend API: <http://localhost/api/>
- Django Admin: <http://localhost/admin/>

### Development Setup

#### Backend

1. Create a virtual environment:

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

1. Install dependencies:

```bash
cd backend
pip install -r requirements.txt
```

1. Run migrations:

```bash
python manage.py migrate
```

#### Frontend

1. Install dependencies:

```bash
cd frontend
npm install
```

1. Start development server:

```bash
npm run dev
```

### Project Structure

```bash
transcribe/
├── backend/
│   ├── core/           # Main Django app
│   ├── transcribe/     # Django project settings
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   └── lib/
│   └── package.json
└── docker-compose.yml
```

### API Documentation

The API documentation is available at `/api/` when running the development server. Key endpoints include:

- `/api/entries/` - Audio file entries management
- `/api/auth/token/` - JWT token authentication
- `/api/documents/` - Document management
- `/api/notes/` - Notes management

### Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### License

This project is licensed under the MIT License - see the LICENSE file for details.

### Acknowledgments

- [Demucs](https://github.com/facebookresearch/demucs) for audio source separation
- [Django REST framework](https://www.django-rest-framework.org/) for API development
- [React](https://reactjs.org/) and [TypeScript](https://www.typescriptlang.org/) for frontend development
