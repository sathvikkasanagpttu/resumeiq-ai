# ResumeIQ Deployment & Operations Guide

This guide covers deployment procedures for **ResumeIQ: Evidence-First AI Resume & Job Matching Engine**, ranging from local developer setups to containerized production deployments using Docker Compose.

---

## 1. Prerequisites

- **Python:** 3.11+ (tested on Python 3.11, 3.12, 3.14)
- **Node.js:** 18.0+ & npm 9+
- **Docker & Docker Compose:** Required for containerized multi-tier deployment
- **PostgreSQL (Optional for local dev):** Version 15+ (SQLite is used seamlessly by default for local development)
- **Redis (Optional for local dev):** Version 7+

---

## 2. Configuration & Environment Variables

### Backend Configuration (`backend/.env`)

| Variable | Description | Default / Example | Required |
| :--- | :--- | :--- | :--- |
| `PROJECT_NAME` | Service display name | `ResumeIQ` | No |
| `ENVIRONMENT` | Deployment environment (`development` / `production`) | `development` | No |
| `SECRET_KEY` | Cryptographic secret for signing JWTs | `ChangeMeInProductionSecretKey123!` | Yes in Prod |
| `ALGORITHM` | JWT signing algorithm | `HS256` | No |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Session validity duration | `1440` (24h) | No |
| `DATABASE_URL` | Database connection URI | `sqlite:///./resumeiq.db` or `postgresql://...` | Yes |
| `REDIS_URL` | Redis cache and queue broker URI | `redis://localhost:6379/0` | No |
| `GEMINI_API_KEY` | Google GenAI API key for embeddings/LLM | (Empty string uses offline vector projection) | Optional |
| `BACKEND_CORS_ORIGINS` | Permitted CORS origins (JSON array) | `["http://localhost:5173", "http://localhost:3000"]` | No |

### Frontend Configuration (`frontend/.env`)

| Variable | Description | Default / Example | Required |
| :--- | :--- | :--- | :--- |
| `VITE_API_URL` | Base backend API endpoint | `http://localhost:8000/api/v1` | Yes |

---

## 3. Local Development Setup

### 3.1 Backend Service

1. **Navigate to the backend directory:**
   ```bash
   cd backend
   ```

2. **Create and activate a virtual environment:**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

4. **Initialize Database & Apply Migrations:**
   ```bash
   alembic upgrade head
   ```

5. **Start the FastAPI server:**
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```
   The backend API will be accessible at:
   - Base URL: `http://localhost:8000`
   - Swagger UI: `http://localhost:8000/docs`
   - ReDoc: `http://localhost:8000/redoc`

---

### 3.2 Frontend Application

1. **Navigate to the frontend directory:**
   ```bash
   cd frontend
   ```

2. **Install Node dependencies:**
   ```bash
   npm install
   ```

3. **Start the Vite development server:**
   ```bash
   npm run dev
   ```
   The frontend UI will be live at:
   - Web App: `http://localhost:5173`

4. **Default Demo Credentials:**
   - **Email:** `demo@resumeiq.ai`
   - **Password:** `ResumeIQ2026!`

---

## 4. Production Deployment via Docker Compose

ResumeIQ includes a production-grade multi-container `docker-compose.yml` orchestrating PostgreSQL 16, Redis 7, the FastAPI backend, and an Nginx-backed React frontend.

### 4.1 Launching the Stack

1. **Ensure environment files are prepared:**
   ```bash
   cp backend/.env.example backend/.env
   ```

2. **Build and start all containers:**
   ```bash
   docker-compose up --build -d
   ```

3. **Verify running containers:**
   ```bash
   docker-compose ps
   ```

### 4.2 Services Architecture

```
Internet / User
      │
      ▼
┌───────────────────────────────┐
│     Frontend (Nginx)          │  Port: 3000
│     React 18 + SPA Router     │
└───────────────┬───────────────┘
                │ /api/v1 (Proxied)
                ▼
┌───────────────────────────────┐
│     Backend (FastAPI)         │  Port: 8000
│     Uvicorn Multi-worker      │
└───────┬───────────────┬───────┘
        │               │
        ▼               ▼
┌──────────────┐ ┌──────────────┐
│  PostgreSQL  │ │    Redis     │
│  Version 16  │ │  Version 7   │
│  Port: 5432  │ │  Port: 6379  │
└──────────────┘ └──────────────┘
```

---

## 5. Database Migration Management

ResumeIQ uses Alembic for database schema versioning.

- **Apply all pending migrations:**
  ```bash
  cd backend
  alembic upgrade head
  ```

- **Generate a new auto-detected migration:**
  ```bash
  alembic revision --autogenerate -m "Add new column to resumes"
  ```

- **Roll back the most recent migration:**
  ```bash
  alembic downgrade -1
  ```

---

## 6. Health Checks & Monitoring

### Health Endpoint
Monitor service availability via:
```bash
curl -f http://localhost:8000/api/v1/health
```
Expected output:
```json
{
  "status": "healthy",
  "database": "connected",
  "vector_store": "ready",
  "version": "1.0.0"
}
```

### Metrics Endpoint
Query operational metrics:
```bash
curl http://localhost:8000/api/v1/metrics
```

---

## 7. Security Hardening Best Practices

1. **Rotate Secrets:** Always replace default values for `SECRET_KEY` and database passwords in production.
2. **TLS / HTTPS:** Ensure all external traffic is terminated via TLS reverse proxy (e.g., Cloudflare, AWS ALB, or Let's Encrypt Nginx).
3. **CORS Whitelisting:** Constrain `BACKEND_CORS_ORIGINS` strictly to authorized domain names.
4. **File Upload Limits:** The backend enforces a strict 10MB file limit on uploaded resumes to prevent Denial of Service (DoS) attacks.
