# Job Application Agent – Development Tasks

## Project Overview

This project is a backend service that automates large parts of the job application workflow using AI agents.

The system will:

• discover job listings in India  
• analyze job descriptions  
• match them with a resume  
• generate optimized resumes  
• generate cover letters  
• automatically apply to jobs when possible  
• store applications and job data in a database  

The goal is to **reduce manual effort in job applications** while maintaining compliance with platform policies.

Automatic applications should occur **only when the job application does not require authentication or manual login**.  
If login or credentials are required, the job should be **stored in the database and the user should be notified by email with the job link**.

Currently the system is designed **for a single user (the developer)** but should be structured so that later it can support **multiple users uploading resumes**.

The resume will initially be provided via a **Google Drive link**.

---

## Core Technologies

Backend framework:

- FastAPI

AI / Agent Framework:

- LangChain
- LangGraph
- Gemini API

Database:

- Neon PostgreSQL

Automation:

- Playwright

Infrastructure:

- Upstash Redis (task queue / caching)

Language:

- Python

Environment:

- Linux

Email Notifications:
-SMTP based email service

---

## Resume Source

The resume will be provided using a **Google Drive public link**.

The agent must:

• download the resume  
• parse its contents  
• extract relevant information  

Extracted data should include:

- skills
- technologies
- projects
- experience
- preferred roles

This parsed resume will be used as the base context for job matching and resume rewriting.

---

## Project Structure

The agent should maintain this structure:

```tree

backend/

app/
├── main.py
│
├── agents/
│   ├── job_search_agent.py
│   ├── jd_analysis_agent.py
│   ├── resume_agent.py
│   └── application_agent.py
│
├── services/
│   ├── llm_service.py
│   ├── scraper_service.py
│   ├── browser_service.py
│   ├── resume_service.py
│   └── email_service.py
│
├── database/
│   ├── models.py
│   ├── session.py
│   └── migrations/
│
├── schemas/
│   └── job_schema.py
│
├── api/
│   └── routes.py
│
└── core/
├── config.py
└── prompts.py

```

---

## Primary Development Tasks

## Task 1 – FastAPI Application Setup

Create the base FastAPI application.

Requirements:

- health endpoint
- environment configuration
- logging
- structured settings

Example endpoint:

```text

GET /health

```

Response:

```json

{
"status": "ok"
}

```

---

## Task 2 – Database Integration

Integrate Neon PostgreSQL.

Requirements:

• async SQLAlchemy  
• database session management  
• models for job records  

Initial tables:

### jobs

Fields:

- id
- title
- company
- job_description
- source_url
- location
- created_at

### applications

Fields:

- id
- job_id
- resume_path
- cover_letter
- status
- applied_at
- created_at

### job_notifications

Fields:

- id
- job_id
- notification_sent
- created_at

---

## Task 3 – Resume Context Loader

Create a service that loads and parses the resume from a Google Drive link.

Responsibilities:

• download resume file  
• extract skills  
• extract technologies  
• extract experience  
• extract project information  

Output example:

```json

{
"skills": ["React", "Node.js", "FastAPI"],
"experience": "Software Developer Intern",
"projects": ["Daily Quizzes"]
}

```

---

## Task 4 – Job Discovery Agent

Create an agent responsible for discovering job listings **in India only**.

Responsibilities:

• search job boards  
• fetch job pages  
• extract job descriptions  
• extract job location  
• filter only India-based jobs  

Tools used:

- Playwright
- HTTP requests
- HTML parsing

Output example:

```json

{
"title": "Software Engineer",
"company": "Example Corp",
"jd_text": "...",
"source": "LinkedIn",
"location": "India",
"apply_url": "..."
}

```

Store results in the database.

---

## Task 5 – Job Description Analysis Agent

Create an LLM agent that evaluates a job description.

Responsibilities:

• extract required skills  
• calculate resume match score  
• identify missing skills  

Example output:

```json

{
"match_score": 0.78,
"required_skills": ["React", "PostgreSQL"],
"missing_skills": ["AWS"]
}

```

Use LangChain with Gemini.

---

## Task 6 – Resume Adaptation Agent

This agent modifies the resume based on the job description.

Responsibilities:

• highlight relevant experience  
• rephrase project descriptions  
• align resume with job requirements  

Output:

- tailored resume
- markdown or PDF version

---

## Task 7 – Cover Letter Generator

Generate a short cover letter.

Inputs:

- job title
- company
- resume
- job description

Output:

150–200 words.

---

## Task 8 – Application Manager

Responsible for submitting or storing applications.

Responsibilities:

• attempt automatic job application when possible  
• detect whether login is required  
• if login is required, skip auto-apply  
• store the job link in the database  
• send notification email to the user  

Status options:

```text

generated
applied
requires_manual_apply
rejected

```

---

## Auto Application Logic

The agent should attempt auto-application only if:

• the job page provides a direct application form  
• no authentication or login is required  

Steps:

1. open application page
2. fill form automatically if possible
3. upload resume
4. submit application

If login is required:

• store the job in the database  
• send email notification to the user  
• include job link and job details  

---

## Agent Workflow

The pipeline should follow this order:

```text

Job Discovery
↓
JD Analysis
↓
Resume Adaptation
↓
Cover Letter Generation
↓
Auto Apply Attempt
↓
Store Application Result

```

---

## LangGraph Agent Flow

Use LangGraph to orchestrate agents.

Graph example:

```text

job_search
↓
jd_analysis
↓
resume_rewrite
↓
cover_letter
↓
auto_apply
↓
store_application

```

Each node should be implemented as an independent function.

---

## API Endpoints

Minimum endpoints required:

### Discover Jobs

```text

POST /agent/discover

```

Triggers job discovery.

---

### Analyze Job

```text

POST /agent/analyze

```

Runs JD analysis.

---

### Generate Application

```text

POST /agent/apply

```

Generates resume and cover letter and attempts application.

---

### List Jobs

```text

GET /jobs

```

Returns stored jobs.

---

## Constraints

The system must:

• search for jobs in India only  
• automatically apply when login is not required  
• skip auto application if authentication is required  
• store skipped jobs in the database  
• notify the user by email with job links  
• maintain modular agent architecture  
• support future multi-user support  

---

## Future Extensions

Possible improvements:

• multi-user support  
• resume upload portal  
• dashboard UI  
• automated interview preparation  
• job ranking model  
• resume improvement suggestions  

---

## Developer Context

The current developer profile:

- Full stack developer
- MERN stack
- FastAPI
- AI integrations
- Docker / infrastructure

The agent should prioritize jobs matching this stack.

---

## Expected Output

The backend should eventually support the workflow:

```text
resume → job search → analysis → resume rewrite → cover letter → auto apply → store in database
```

The code should remain modular and maintainable.

---

## Notes for the Coding Agent

Follow these principles:

- keep services independent  
- avoid tightly coupled modules  
- prefer async code  
- document all agents clearly
- Do not write unnecessary comments.

Focus on building a **stable backend agent pipeline first**
