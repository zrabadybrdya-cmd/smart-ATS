import logging
from celery import shared_task
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_notification_email(self, subject: str, template_name: str, context: dict, recipient_list: list):
    try:
        html_content = render_to_string(template_name, context)
        text_content = strip_tags(html_content)

        from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', settings.EMAIL_HOST_USER)
        email = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=from_email,
            to=recipient_list
        )
        email.attach_alternative(html_content, "text/html")

        email.send(fail_silently=False)
        logger.info(f"Email successfully sent to {recipient_list} with subject '{subject}'")
        return f"Email sent to {recipient_list}"

    except Exception as exc:
        logger.error(f"Error sending email to {recipient_list}: {exc}")
        raise self.retry(exc=exc)