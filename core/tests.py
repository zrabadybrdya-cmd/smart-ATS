from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase
from django.test import TestCase
from core.models import ApplicationStatus
from core.state_machine import ApplicationStateMachine

User = get_user_model()

class DummyApplication:
    def __init__(self, status):
        self.status = status

class StateMachineTests(TestCase):
    
    def test_valid_transitions(self):
        self.assertTrue(ApplicationStateMachine.is_valid_transition(
            ApplicationStatus.PENDING, ApplicationStatus.REVIEWING
        ))
        self.assertTrue(ApplicationStateMachine.is_valid_transition(
            ApplicationStatus.REVIEWING, ApplicationStatus.SHORTLISTED
        ))
        self.assertTrue(ApplicationStateMachine.is_valid_transition(
            ApplicationStatus.SHORTLISTED, ApplicationStatus.REJECTED
        ))

    def test_invalid_transitions(self):
        self.assertFalse(ApplicationStateMachine.is_valid_transition(
            ApplicationStatus.PENDING, ApplicationStatus.ACCEPTED
        ))
        self.assertFalse(ApplicationStateMachine.is_valid_transition(
            ApplicationStatus.REJECTED, ApplicationStatus.REVIEWING
        ))
        self.assertFalse(ApplicationStateMachine.is_valid_transition(
            ApplicationStatus.PENDING, ApplicationStatus.PENDING
        ))

    def test_transition_method_success(self):
        app = DummyApplication(status=ApplicationStatus.PENDING)
        ApplicationStateMachine.transition(app, ApplicationStatus.REVIEWING)
        self.assertEqual(app.status, ApplicationStatus.REVIEWING)

    def test_transition_method_failure(self):
        app = DummyApplication(status=ApplicationStatus.PENDING)
        with self.assertRaises(ValueError):
            ApplicationStateMachine.transition(app, ApplicationStatus.ACCEPTED)