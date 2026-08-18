from core.models import ApplicationStatus

class ApplicationStateMachine:
    ALLOWED_TRANSITIONS = {
        ApplicationStatus.PENDING: [
            ApplicationStatus.REVIEWING,
            ApplicationStatus.REJECTED
        ],
        ApplicationStatus.REVIEWING: [
            ApplicationStatus.SHORTLISTED,
            ApplicationStatus.REJECTED
        ],
        ApplicationStatus.SHORTLISTED: [
            ApplicationStatus.ACCEPTED,
            ApplicationStatus.REJECTED
        ],
        ApplicationStatus.ACCEPTED: [],
        ApplicationStatus.REJECTED: [],
    }

    @classmethod
    def is_valid_transition(cls, current_status, new_status):
        if current_status == new_status:
            return False
        
        allowed_statuses = cls.ALLOWED_TRANSITIONS.get(current_status, [])
        return new_status in allowed_statuses

    @classmethod
    def transition(cls, application, new_status):
        if not cls.is_valid_transition(application.status, new_status):
            raise ValueError(
                f"تغییر وضعیت غیرمجاز: نمی‌توان درخواست را از وضعیت '{application.status}' به '{new_status}' تغییر داد."
            )
        
        application.status = new_status
        return application