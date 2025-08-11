"""
URL configuration for the API app.
"""

from django.urls import path
from .ninja_api import api

urlpatterns = [
    path("api/", api.urls),
]
