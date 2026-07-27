from django.contrib import admin
from django.urls import path
from core.views import HRTestView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/hr-test/', HRTestView.as_view(), name='hr-test'),
]