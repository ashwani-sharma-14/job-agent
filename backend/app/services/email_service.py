import re
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from loguru import logger

from app.core.config import get_settings

settings = get_settings()

EMAIL_PATTERN = re.compile(
    r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b"
)

IGNORE_EMAIL_DOMAINS = [
    "example.com", "test.com", "email.com", "domain.com",
    "gmail.com", "yahoo.com", "outlook.com", "hotmail.com",
    "linkedin.com", "indeed.com",
]


def extract_hr_emails(text: str) -> list[str]:
    if not text:
        return []
    emails = EMAIL_PATTERN.findall(text)
    filtered = []
    for email in emails:
        domain = email.split("@")[1].lower()
        if domain not in IGNORE_EMAIL_DOMAINS:
            filtered.append(email.lower())
    return list(set(filtered))


async def send_hr_application(
    hr_email: str,
    job_title: str,
    company: str,
    cover_letter: str,
    resume_url: str,
) -> bool:
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"Application for {job_title} — Ashwani Sharma"
        msg["From"] = settings.SMTP_USER
        msg["To"] = hr_email

        text = f"""Dear Hiring Manager,

I am writing to express my interest in the {job_title} position at {company}.

{cover_letter}

Resume: {resume_url}

Best regards,
Ashwani Sharma
{settings.SMTP_USER}
"""

        html = f"""
<html>
<body style="font-family: Arial, sans-serif; padding: 20px; line-height: 1.6;">
    <p>Dear Hiring Manager,</p>
    <p>I am writing to express my interest in the <strong>{job_title}</strong> position at <strong>{company}</strong>.</p>
    <div style="margin: 15px 0; padding: 15px; background: #f9f9f9; border-left: 4px solid #2196F3;">
        {cover_letter.replace(chr(10), '<br>')}
    </div>
    <p><strong>Resume:</strong> <a href="{resume_url}">{resume_url}</a></p>
    <p>Best regards,<br>
    <strong>Ashwani Sharma</strong><br>
    {settings.SMTP_USER}</p>
</body>
</html>
"""

        msg.attach(MIMEText(text, "plain"))
        msg.attach(MIMEText(html, "html"))

        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
            server.starttls()
            server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            server.send_message(msg)

        logger.info("HR application sent to {} for {} at {}", hr_email, job_title, company)
        return True

    except Exception as e:
        logger.error("Failed to send HR email to {}: {}", hr_email, e)
        return False


async def send_job_notification(
    job_title: str, company: str, job_url: str, job_description: str = ""
) -> bool:
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"New Job Match: {job_title} at {company}"
        msg["From"] = settings.SMTP_USER
        msg["To"] = settings.NOTIFICATION_EMAIL

        text = f"""New Job Match Found!

Title: {job_title}
Company: {company}
Link: {job_url}

This job requires manual application.

{f"Description: {job_description[:500]}..." if job_description else ""}
"""

        html = f"""
<html>
<body style="font-family: Arial, sans-serif; padding: 20px;">
    <h2 style="color: #2196F3;">New Job Match Found!</h2>
    <table style="border-collapse: collapse;">
        <tr><td><strong>Title:</strong></td><td>{job_title}</td></tr>
        <tr><td><strong>Company:</strong></td><td>{company}</td></tr>
        <tr><td><strong>Link:</strong></td><td><a href="{job_url}">{job_url}</a></td></tr>
    </table>
    <p style="color: #e67e22;"><strong>This job requires manual application.</strong></p>
    {f'<p><strong>Description:</strong><br>{job_description[:500]}...</p>' if job_description else ''}
</body>
</html>
"""

        msg.attach(MIMEText(text, "plain"))
        msg.attach(MIMEText(html, "html"))

        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
            server.starttls()
            server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            server.send_message(msg)

        logger.info("Notification sent for: {} at {}", job_title, company)
        return True

    except Exception as e:
        logger.error("Failed to send notification: {}", e)
        return False
