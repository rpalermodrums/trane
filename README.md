# Trane

> Test Kitchen for Experiments at the Intersection of Music, AI, Sound, and Technology

## Modules

### Transcribe - Audio Source Separation Tool

#### Overview

Transcribe is a full-stack application that provides audio source separation capabilities using the Demucs model. It offers both a web interface and a CLI tool for processing audio files.

#### Features

- Audio source separation using multiple Demucs models
- CLI interface for batch processing
- Real-time progress tracking
- Audio player with track management

### Stack

#### Backend (Django + Celery)

- Django REST framework for API endpoints
- Celery for asynchronous task processing
- Channels for WebSocket communication
- PostgreSQL for data storage
- Redis for task queue and WebSocket backend

#### Frontend (React + TypeScript)

- React with TypeScript for type safety
- TanStack Query for data fetching
- WebSocket integration for real-time updates
- Tailwind CSS for styling
- Shadcn UI components

### Installation

#### Prerequisites

- Docker and Docker Compose
- Node.js 20+ (for local development)
- Python 3.10+ (for local development)

#### Quick Start

1 . Clone the repository:

```bash
git clone https://github.com/yourusername/transcribe.git
cd transcribe
```

2 . Create a `.env` file in the root directory:

```bash
DEBUG=1
DJANGO_SECRET_KEY=your-secret-key
POSTGRES_DB=database
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
REDIS_HOST=redis
REDIS_PORT=6379
```

3 . Build and start the containers:

```bash
docker compose up -d --build
```

4 . Create a superuser for Django admin:

```bash
docker compose exec backend python manage.py createsuperuser
```

5 . Access the application:

- Frontend: <http://localhost>
- Backend API: <http://localhost/api/>
- Django Admin: <http://localhost/admin/>

### Development Setup

#### Backend

1 . Create a virtual environment:

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2 . Install dependencies:

```bash
cd backend
pip install -r requirements.txt
```

3 . Run migrations:

```bash
python manage.py migrate
```

#### Frontend

1 . Install dependencies:

```bash
cd frontend
npm install
```

2 . Start development server:

```bash
npm run dev
```

### Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### License

This project is licensed under the GNU General Public License (GPL) Ver3 - see the [LICENSE](LICENSE) file for details.

### Acknowledgments

- [Demucs](https://github.com/facebookresearch/demucs) for audio source separation
- [PyTorch](https://pytorch.org/) for deep learning
- [Django](https://www.djangoproject.com/) and [Django REST framework](https://www.django-rest-framework.org/) for backend development
- [React](https://reactjs.org/) and [TypeScript](https://www.typescriptlang.org/) for frontend development
