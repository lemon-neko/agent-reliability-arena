"""Celery worker entry points. Task arguments contain IDs, never model secrets."""

from celery import Celery

from arena.application.service import ArenaService
from arena.infrastructure.config import settings

celery_app = Celery("arena", broker=settings.redis_url, backend=settings.redis_url)
celery_app.conf.update(
    task_always_eager=settings.celery_task_always_eager,
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    worker_prefetch_multiplier=1,
    result_expires=3600,
)


@celery_app.task(bind=True, autoretry_for=(RuntimeError,), retry_backoff=True, max_retries=3)
def run_tournament(_task, tournament_id: str) -> None:
    ArenaService.create(settings).execute_tournament(tournament_id)


@celery_app.task(bind=True, autoretry_for=(RuntimeError,), retry_backoff=True, max_retries=2)
def run_assessment(_task, assessment_id: str) -> None:
    ArenaService.create(settings).execute_assessment(assessment_id)
