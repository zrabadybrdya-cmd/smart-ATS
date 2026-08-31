import logging
import smtplib
import socket
from celery import shared_task
from celery.exceptions import MaxRetriesExceededError
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_notification_email(
    self,
    subject: str,
    template_name: str,
    context: dict,
    recipient_list: list,
):
    current_attempt = self.request.retries + 1
    logger.info(
        f"[Task {self.request.id}] شروع ارسال ایمیل به {recipient_list} (تلاش {current_attempt}/{self.max_retries + 1})"
    )

    try:
        html_content = render_to_string(template_name, context)
        text_content = strip_tags(html_content)

        from_email = getattr(
            settings, 'DEFAULT_FROM_EMAIL', settings.EMAIL_HOST_USER
        )

        email = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=from_email,
            to=recipient_list,
        )
        email.attach_alternative(html_content, "text/html")

        email.send(fail_silently=False)

        logger.info(
            f"[Task {self.request.id}] ایمیل با موفقیت به {recipient_list} ارسال شد."
        )
        return f"Email successfully sent to {recipient_list}"

    except (
        smtplib.SMTPException,
        socket.error,
        TimeoutError,
        ConnectionError,
    ) as conn_exc:
        logger.warning(
            f"[Task {self.request.id}] خطای ارتباطی در ارسال ایمیل: {conn_exc}. آماده‌سازی برای تلاش مجدد...",
            exc_info=True,
        )
        try:
            raise self.retry(exc=conn_exc, countdown=60 * current_attempt)
        except MaxRetriesExceededError:
            logger.error(
                f"[Task {self.request.id}] حداکثر دفعات تلاش مجدد ({self.max_retries}) برای {recipient_list} به پایان رسید.",
                exc_info=True,
            )
            raise

    except Exception as exc:
        logger.error(
            f"[Task {self.request.id}] خطای غیرمنتظره در ارسال ایمیل: {exc}",
            exc_info=True,
        )
        raise exc