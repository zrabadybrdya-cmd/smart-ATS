from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

User = get_user_model()

class RBACTestCase(APITestCase):
    def setUp(self):
        self.hr_user = User.objects.create_user(email='hr@example.com', password='password123', role='hr')
        self.candidate_user = User.objects.create_user(email='candidate@example.com', password='password123', role='candidate')

    def test_candidate_cannot_access_hr_view(self):
        self.client.force_authenticate(user=self.candidate_user)
        response = self.client.get('/api/hr-test/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        