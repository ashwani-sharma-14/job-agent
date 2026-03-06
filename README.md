# 🤖 AI JobAgent

A fully automated, end-to-end AI job hunting system. JobAgent constantly searches for the latest software engineering roles, evaluates them using LLMs, and autonomously applies to jobs that are a strong match for your resume.

## 🌟 Key Features

- **Multi-Source Scraping**: Discovers jobs from Adzuna, Remotive, Jobicy, Arbeitnow, JSearch, The Muse, and LinkedIn.
- **AI Data Cleaning**: Uses Gemini LLMs to parse messy job descriptions, extract precise fields, and normalize data (HTML stripping, missing defaults).
- **Intelligent Analysis**: LangGraph-powered AI evaluates job descriptions against your resume, calculating a "Match Score" based on required vs. missing skills.
- **Autonomous Auto-Apply**: Uses Playwright headless browsers to automatically navigate applications, answer standard form fields, attach your resume, and submit.
- **Smart Rate Limiting**: Implements a strict 4-phase hourly cycle (Discover -> Clean -> Analyze -> Apply) to respect API quotas and LLM daily limits.
- **Next.js Dashboard**: A beautiful, dark-mode visual interface to monitor sourced jobs, track match scores, and manually trigger pipeline phases.

---

## 🏗️ Project Architecture

```text
jobagent/
├── backend/                  # FastAPI & LangGraph AI Backend
│   ├── app/                 
│   │   ├── agents/           # LangGraph nodes (Job Search, Resume Analysis, Apply)
│   │   ├── api/              # FastAPI Routes (/agent/discover, /agent/apply)
│   │   ├── core/             # Database configs & LLM Prompts
│   │   ├── models/           # SQLAlchemy DB Models
│   │   └── services/         # Playwright, Upstash Redis, Mailer, etc.
│   ├── Dockerfile            # Configured to host Playwright + Python on Render
│   └── render.yaml           # Automated Render.com Blueprint Deployment
│
└── frontend/                 # Next.js 15 Web Dashboard
    ├── src/
    │   ├── app/              # Main Dashboard Page
    │   ├── components/       # JobCards & PipelineControls
    │   └── lib/              # API connections to FastAPI
    └── package.json
```

---

## 🚀 Quickstart Local Setup

### 1. Database & Services

You will need a PostgreSQL database and an Upstash Redis database.

- Create a free Postgres database (e.g., Neon.tech, Supabase).
- Create a free Redis database at Upstash.com.
- Obtain a Gemini API key from Google AI Studio.
- (Optional) Get Adzuna and RapidAPI (JSearch) keys.

### 2. Backend Setup

The backend uses `uv` for lightning-fast Python package management.

```bash
cd backend
curl -LsSf https://astral.sh/uv/install.sh | sh
uv sync
uv run uvicorn app.main:app --reload
```

### 3. Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

Visit `http://localhost:3000` to access the JobAgent dashboard!

---

## ⚙️ Environment Variables

Create a `.env` file inside the `backend/` directory.

### Example `.env`

```ini
# ==========================================
# Core AI Configuration
# ==========================================
# Google Gemini API key used for Analysis and Data Cleaning
GEMINI_API_KEY="AIzaSyYourGeminiApiKeyHere123abc"

# ==========================================
# Database Connections
# ==========================================
# PostgreSQL connection string (Asyncpg format required)
DATABASE_URL="postgresql+asyncpg://user:password@aws-0-us-west-2.neon.tech/jobagent?ssl=require"

# Upstash Redis REST connection used to stage raw scraped jobs
UPSTASH_REDIS_REST_URL="https://your-upstash-url.upstash.io"
UPSTASH_REDIS_REST_TOKEN="YourUpstashToken123"

# ==========================================
# Job Board APIs
# ==========================================
ADZUNA_APP_ID="your_adzuna_id"
ADZUNA_APP_KEY="your_adzuna_key"
RAPIDAPI_KEY="your_rapidapi_key"  # For JSearch

# ==========================================
# Application Configuration
# ==========================================
# Gmail details used by the AI to email resumes if a site requires it
SMTP_USER="your.email@gmail.com"
SMTP_PASSWORD="your-google-app-password"

# Publicly accessible link to your PDF resume (Drive, Dropbox, etc.)
GOOGLE_DRIVE_RESUME_URL="https://drive.google.com/file/d/your_pdf_id/view?usp=sharing"

# ==========================================
# Rate Limits (Optional Overrides)
# ==========================================
DAILY_JOB_LIMIT="400"
LLM_RPM_LIMIT="25"
LLM_DAILY_LIMIT="14000"
```

---

## ☁️ Deployment

### Backend (Render)

Because JobAgent uses Playwright headless browsers to apply to jobs, it requires a persistent container.

1. Link this repository to **Render.com** as a Blueprint.
2. Render will automatically read `render.yaml` and the `Dockerfile` to deploy the background worker securely on the free tier.

### Frontend (Vercel)

Deploy the Next.js `frontend` directory natively to Vercel and point your API URLs to the newly generated `.onrender` URL.
