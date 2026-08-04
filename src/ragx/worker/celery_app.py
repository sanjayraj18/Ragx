from celery import Celery

from ragx.config import get_settings

settings = get_settings()

celery_app = Celery("ragx", broker=str(settings.redis_url), include=["ragx.worker.tasks"])

celery_app.conf.update(
    # at-least-once delivery: a message survives its worker's death
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    worker_prefetch_multiplier=1,
    task_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
)
