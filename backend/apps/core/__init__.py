# Core app - Base functionality for OMS Trading
from .celery import app as celery_app

celery = celery_app
__all__ = ("celery_app", "celery")
