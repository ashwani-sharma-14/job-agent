JD_ANALYSIS_PROMPT = """You are a job match analyzer for a fresher/entry-level full-stack developer.

Candidate Profile:
{resume_context}

Job Description:
{job_description}

Analyze this job against the candidate. Consider:
1. The candidate is a fresher/entry-level developer
2. Focus on skill overlap with: Python, FastAPI, React, Node.js, MERN stack, AI/ML
3. Internships and entry-level roles are highly desirable
4. YC startups and modern tech companies are preferred

You MUST return ONLY a valid JSON object (no markdown, no explanation) with exactly these fields:
{{
    "match_score": <float 0.0 to 1.0>,
    "required_skills": ["skill1", "skill2"],
    "missing_skills": ["skill1"],
    "is_fresher_friendly": <true/false>,
    "recommendation": "apply" or "skip"
}}

Scoring guide:
- 0.7-1.0: Strong match, relevant stack, fresher-friendly
- 0.4-0.7: Partial match, some relevant skills
- 0.0-0.4: Poor match, senior role, or unrelated stack
"""

RESUME_REWRITE_PROMPT = """Rewrite this resume to match the target job description.

Original Resume:
{resume_context}

Target Job Description:
{job_description}

Guidelines:
- Highlight relevant experience and skills
- Rephrase project descriptions to align with job requirements
- Keep content truthful, only reorganize and rephrase
- Output in clean markdown format
"""

COVER_LETTER_PROMPT = """Write a concise, professional cover letter (150–200 words).

Job Title: {job_title}
Company: {company}
Job Description: {job_description}
Candidate Resume: {resume_context}

The letter should be personalized, confident, and specific to the role.
"""

RESUME_PARSE_PROMPT = """Extract structured information from this resume text. Parse everything carefully.

Resume:
{resume_text}

You MUST return ONLY a valid JSON object (no markdown, no explanation) with exactly these fields:
{{
    "name": "Full Name",
    "skills": ["skill1", "skill2"],
    "technologies": ["tech1", "tech2"],
    "experience": ["Job Title at Company"],
    "projects": ["Project Name - brief description"],
    "preferred_roles": ["Role 1", "Role 2"]
}}
"""

JOB_CLEAN_PROMPT = """Extract clean, structured job information from this raw listing data.

Raw data:
{raw_job}

You MUST return ONLY a valid JSON object (no markdown, no explanation) with exactly these fields:
{{
    "title": "Clean job title",
    "company": "Company name",
    "location": "City, Country or Remote",
    "description": "Clean plain-text job description (no HTML)"
}}

Rules:
- Remove all HTML tags from description
- If company is missing, try to extract from description or title
- If location is missing, use "Remote"
- Keep description concise but complete (max 3000 chars)
"""
