from datetime import datetime, timezone

from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.models import Job, Application, JobNotification
from app.services.browser_service import check_requires_login, attempt_form_fill
from app.services.email_service import send_job_notification, send_hr_application, extract_hr_emails
from app.agents.resume_agent import rewrite_resume, generate_cover_letter
from app.core.config import get_settings

settings = get_settings()


async def process_application(job: Job, db: AsyncSession) -> dict:
    cover_letter = await generate_cover_letter(
        job_title=job.title,
        company=job.company,
        job_description=job.job_description or "",
    )

    hr_emails = extract_hr_emails(job.job_description or "")

    if hr_emails:
        hr_email = hr_emails[0]
        sent = await send_hr_application(
            hr_email=hr_email,
            job_title=job.title,
            company=job.company,
            cover_letter=cover_letter,
            resume_url=settings.GOOGLE_DRIVE_RESUME_URL,
        )

        application = Application(
            job_id=job.id,
            cover_letter=cover_letter,
            status="emailed_hr" if sent else "email_failed",
            applied_at=datetime.now(timezone.utc) if sent else None,
        )
        db.add(application)
        await db.flush()

        logger.info("Emailed HR at {} for '{}' at {} — sent: {}", hr_email, job.title, job.company, sent)
        return {"status": "emailed_hr", "job": job.title, "hr_email": hr_email, "sent": sent}

    requires_login = False
    if job.source_url:
        requires_login = await check_requires_login(job.source_url)

    if requires_login:
        application = Application(
            job_id=job.id,
            cover_letter=cover_letter,
            status="requires_manual_apply",
        )
        db.add(application)

        notification = JobNotification(job_id=job.id, notification_sent=False)
        db.add(notification)
        await db.flush()

        sent = await send_job_notification(
            job_title=job.title,
            company=job.company,
            job_url=job.source_url or "",
            job_description=job.job_description or "",
        )
        if sent:
            notification.notification_sent = True

        logger.info("Job '{}' requires manual apply — notification sent: {}", job.title, sent)
        return {"status": "requires_manual_apply", "job": job.title, "notified": sent}

    tailored_resume = await rewrite_resume(job.job_description or "")
    applied = False
    if job.source_url:
        applied = await attempt_form_fill(
            job.source_url,
            {"name": "Ashwani Sharma", "email": settings.SMTP_USER, "resume": tailored_resume},
        )

    application = Application(
        job_id=job.id,
        cover_letter=cover_letter,
        status="applied" if applied else "generated",
        applied_at=datetime.now(timezone.utc) if applied else None,
    )
    db.add(application)
    await db.flush()

    logger.info("Application for '{}': {}", job.title, application.status)
    return {"status": application.status, "job": job.title}
