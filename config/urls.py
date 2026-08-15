from django.contrib import admin
from django.urls import include, path
from core.views import home_view

urlpatterns = [
    path('', home_view, name='home'),
    path('admin/', admin.site.urls),
    path('api/', include('core.urls')),
]