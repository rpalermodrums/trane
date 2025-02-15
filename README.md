# Trane

**Trane** is a cutting-edge experimental test kitchen at the intersection of machine learning and music. It explores real‑time audio and MIDI analysis, feature extraction, and DSP (Digital Signal Processing) using modern web technologies, Python/Django on the backend, and a React/TypeScript frontend. The project leverages Docker and container orchestration to provide a full-stack, scalable environment.

---

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Features](#features)
- [Getting Started](#getting-started)
  - [Prerequisites](#prerequisites)
  - [Running with Docker Compose](#running-with-docker-compose)
  - [Local Development](#local-development)
- [Backend Details](#backend-details)
- [Frontend Details](#frontend-details)
- [Contributing](#contributing)
- [License](#license)

---

## Overview

Trane is designed as a research and development platform to experiment with real‑time machine learning for audio and MIDI. The project consists of:

- **Backend (Django & DSP Services):**  
  A Django-based REST API, asynchronous tasks powered by Celery, and a DSP service (implemented with Flask and Socket.IO) that processes audio/MIDI data, extracts musical features, and supports real‑time processing.

- **Frontend (Trane UI):**  
  A modern React application built with Vite and TypeScript. It offers an interactive file manager, upload components with drag‑and‑drop support, real‑time status updates, and theme toggling.

- **Infrastructure:**  
  A full Docker Compose setup that orchestrates services including PostgreSQL, Redis, Django, the DSP service, Celery workers, and an Nginx proxy.

---

## Architecture

The Trane system is divided into several containerized services:

- **Postgres:**  
  Stores application data and processing results.

- **Redis:**  
  Used for Celery message brokering, caching, and performance metrics.

- **Django (Backend):**  
  Provides REST endpoints for file uploads, task status, and DSP feature retrieval. It also manages asynchronous processing tasks and stores results in the database.

- **DSP Service:**  
  A Flask-based service (wrapped with Socket.IO for websocket support) that handles real‑time audio and MIDI processing, interacts with Celery tasks, and serves endpoints for live feature updates.

- **Celery Worker:**  
  Processes audio and MIDI files in the background, extracts features using state‑of‑the‑art DSP and ML techniques, and writes performance metrics.

- **Nginx Proxy:**  
  Routes incoming HTTP requests to the appropriate services (e.g., API calls to Django, web requests to the React frontend).

- **Trane UI (Frontend):**  
  A React application that provides a user-friendly interface to upload files, view processing status/results, and interact with projects.

---

## Features

- **File Upload & Management:**  
  Drag‑and‑drop file upload for audio (WAV, MP3, OGG) and MIDI files with real‑time progress feedback.

- **Real‑Time DSP & Feature Extraction:**  
  Process audio streams and files asynchronously with support for both chunked and full‑file processing. Extracted features include pitch, tempo, spectral features, and more.

- **Asynchronous Task Processing:**  
  Celery tasks ensure non‑blocking processing with automatic retries, progress tracking, and Redis‑backed caching of results.

- **WebSocket & Real‑Time Data:**  
  The DSP service supports real‑time communication with the frontend for live updates on synchronized audio and MIDI features.

- **Performance Monitoring:**  
  Built‑in modules track CPU, memory, and GPU usage. Dynamic resource management (via an optimized thread pool and resource manager) allows Trane to adapt processing loads.

- **Modern UI/UX:**  
  Built with React, Vite, and Tailwind CSS, the UI offers theme toggling (light/dark mode), responsive design, and an intuitive file manager interface.

---

## Getting Started

### Prerequisites

- [Docker](https://www.docker.com/get-started) & [Docker Compose](https://docs.docker.com/compose/)
- (Optional) [Node.js](https://nodejs.org/) and [pnpm](https://pnpm.io/) for frontend development

### Running with Docker Compose

1. **Clone the Repository:**

   ```bash
   git clone https://github.com/yourusername/trane.git
   cd trane
   ```

2. **Configure Environment Variables:**

   Create a `.env` file in the repository root (and in `trane-ui/` as needed) with variables for PostgreSQL, Redis, Django, DSP service URL, etc. (See sample values in the provided `.env` files.)

3. **Start the Services:**

   ```bash
   docker-compose up --build
   ```

4. **Access the Services:**

   - **Frontend:** [http://localhost:3000](http://localhost:3000)
   - **Django API:** [http://localhost:8000](http://localhost:8000)
   - **DSP Service (Flask/Socket.IO):** [http://localhost:9000](http://localhost:9000)
   - **Nginx Proxy (Routes to frontend/API):** [http://localhost](http://localhost)

### Local Development

#### Backend

1. Navigate to the `backend/` directory.
2. Create and activate a Python virtual environment.
3. Install dependencies:

   ```bash
   pip install -r requirements.txt
   pip install -r trane/realtime_dsp/requirements_dsp.txt
   ```

4. Run Django migrations:

   ```bash
   python manage.py migrate
   ```

5. Start the Django development server:

   ```bash
   python manage.py runserver 8000
   ```

6. (Optional) Run the DSP service locally if needed.

#### Frontend

1. Navigate to the `trane-ui/` directory.
2. Install dependencies with pnpm:

   ```bash
   pnpm install
   ```

3. Start the development server:

   ```bash
   pnpm dev
   ```

   The application should open at [http://localhost:3000](http://localhost:3000).

---

## Backend Details

- **Django & REST API:**  
  Handles file uploads, creates `ProcessingTask` records, and provides endpoints (`/dsp/upload/`, `/dsp/result/<task_id>/`) for polling processing status and retrieving results.

- **Celery Tasks:**  
  Asynchronously process audio files (with both chunked and complete‑file modes) and MIDI events. Tasks update the `ProcessingTask` and `ProcessingResult` models accordingly.

- **DSP Service:**  
  A Flask-based server with Socket.IO that receives streaming audio and MIDI data, manages real‑time synchronization via buffer managers, and offers live feature extraction endpoints (`/latest_features`).

- **Performance & Resource Optimization:**  
  Modules in `performance.py` and an optimized thread pool adapt processing parameters based on current CPU/GPU and memory usage.

---

## Frontend Details

- **React + Vite + TypeScript:**  
  The frontend is built using a modern stack and provides an intuitive interface for file management, uploading, and monitoring processing tasks.

- **UI Components:**  
  Custom components for file management (FileManager, FileUpload) are built using React, Tailwind CSS, and shadcn‑styled UI elements (e.g., buttons, cards, dropdown menus).

- **Theme Toggle & Routing:**  
  Supports dark/light theme switching and client‑side routing via React Router.

---

## Contributing

Contributions, bug reports, and feature requests are welcome! Please check the [issues](https://github.com/yourusername/trane/issues) page for open tasks or propose your ideas via pull requests.

---

## License

This project is open source and available under the [GNU General Public License](LICENSE).

---
