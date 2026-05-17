"""Scheduled publishing — APScheduler + SQLite persistence.

Jobs survive restarts: every scheduled post is written to SQLite and
re-loaded on startup. APScheduler fires the publish coroutine at the
requested time. A job never raises out of the scheduler — it records
``published`` / ``failed`` with details instead.
"""

from __future__ import annotations

import sqlite3
import threading
import uuid
from datetime import datetime, timezone

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.date import DateTrigger

from ...config import get_settings
from ...logging_conf import get_logger
from .social_exceptions import SchedulingError, SocialError
from .social_models import (
    FacebookPublishInput,
    ScheduledPost,
    ScheduleResult,
    SchedulePostInput,
)

log = get_logger("hackai.social.sched")

_SCHEMA = """
CREATE TABLE IF NOT EXISTS scheduled_posts (
    id            TEXT PRIMARY KEY,
    platform      TEXT NOT NULL,
    image_url     TEXT NOT NULL,
    caption       TEXT NOT NULL,
    scheduled_time TEXT NOT NULL,
    status        TEXT NOT NULL,
    created_at    TEXT NOT NULL,
    post_id       TEXT NOT NULL DEFAULT '',
    error         TEXT NOT NULL DEFAULT ''
);
"""


class SchedulerService:
    """Process-wide scheduler. Start it from the FastAPI lifespan."""

    def __init__(self) -> None:
        self._scheduler: AsyncIOScheduler | None = None
        self._lock = threading.Lock()
        self._conn: sqlite3.Connection | None = None

    # --- persistence ---------------------------------------------------- #
    def _db(self) -> sqlite3.Connection:
        if self._conn is None:
            self._conn = sqlite3.connect(
                get_settings().social_db_path,
                check_same_thread=False,
            )
            self._conn.row_factory = sqlite3.Row
            self._conn.execute(_SCHEMA)
            self._conn.commit()
        return self._conn

    def _row_to_model(self, row: sqlite3.Row) -> ScheduledPost:
        return ScheduledPost(
            id=row["id"],
            platform=row["platform"],
            image_url=row["image_url"],
            caption=row["caption"],
            scheduled_time=datetime.fromisoformat(row["scheduled_time"]),
            status=row["status"],
            created_at=datetime.fromisoformat(row["created_at"]),
            post_id=row["post_id"],
            error=row["error"],
        )

    def _insert(self, post: ScheduledPost) -> None:
        with self._lock:
            self._db().execute(
                "INSERT INTO scheduled_posts VALUES "
                "(:id,:platform,:image_url,:caption,:scheduled_time,"
                ":status,:created_at,:post_id,:error)",
                {
                    "id": post.id,
                    "platform": post.platform,
                    "image_url": post.image_url,
                    "caption": post.caption,
                    "scheduled_time": post.scheduled_time.isoformat(),
                    "status": post.status,
                    "created_at": post.created_at.isoformat(),
                    "post_id": post.post_id,
                    "error": post.error,
                },
            )
            self._db().commit()

    def _update(self, job_id: str, *, status: str, post_id: str = "",
                error: str = "") -> None:
        with self._lock:
            self._db().execute(
                "UPDATE scheduled_posts SET status=?, post_id=?, error=? "
                "WHERE id=?",
                (status, post_id, error, job_id),
            )
            self._db().commit()

    def _get(self, job_id: str) -> ScheduledPost | None:
        cur = self._db().execute(
            "SELECT * FROM scheduled_posts WHERE id=?", (job_id,)
        )
        row = cur.fetchone()
        return self._row_to_model(row) if row else None

    def list_pending(self) -> list[ScheduledPost]:
        cur = self._db().execute(
            "SELECT * FROM scheduled_posts WHERE status='pending'"
        )
        return [self._row_to_model(r) for r in cur.fetchall()]

    # --- lifecycle ------------------------------------------------------ #
    def start(self) -> None:
        if self._scheduler is not None:
            return
        self._scheduler = AsyncIOScheduler(timezone="UTC")
        self._scheduler.start()
        reloaded = 0
        for post in self.list_pending():
            self._add_job(post.id, post.scheduled_time)
            reloaded += 1
        log.info("Scheduler started (%d pending jobs reloaded)", reloaded)

    def shutdown(self) -> None:
        if self._scheduler is not None:
            self._scheduler.shutdown(wait=False)
            self._scheduler = None
        if self._conn is not None:
            self._conn.close()
            self._conn = None

    # --- scheduling ----------------------------------------------------- #
    def _add_job(self, job_id: str, when: datetime) -> None:
        assert self._scheduler is not None
        # Past-due jobs (e.g. reloaded after downtime) run immediately.
        run_at = when
        if when <= datetime.now(timezone.utc):
            run_at = datetime.now(timezone.utc)
        self._scheduler.add_job(
            self._execute,
            trigger=DateTrigger(run_date=run_at),
            args=[job_id],
            id=job_id,
            replace_existing=True,
            misfire_grace_time=3600,
        )

    def schedule(self, data: SchedulePostInput) -> ScheduleResult:
        try:
            post = ScheduledPost(
                id=str(uuid.uuid4()),
                platform=data.platform,
                image_url=str(data.image_url),
                caption=data.caption,
                scheduled_time=data.scheduled_time,
                status="pending",
                created_at=datetime.now(timezone.utc),
            )
            self._insert(post)
        except sqlite3.Error as exc:
            raise SchedulingError(
                details=f"Persistence failed: {exc}"
            ) from exc

        if self._scheduler is None:
            raise SchedulingError(
                "Scheduler is not running.",
                details="Persisted the job; start the API to execute it.",
            )
        self._add_job(post.id, post.scheduled_time)
        log.info("Scheduled %s post %s for %s",
                 post.platform, post.id, post.scheduled_time.isoformat())
        return ScheduleResult(
            job_id=post.id,
            platform=post.platform,
            scheduled_time=post.scheduled_time,
        )

    # --- execution ------------------------------------------------------ #
    async def _execute(self, job_id: str) -> None:
        post = self._get(job_id)
        if post is None or post.status != "pending":
            return
        # Imported here to avoid any import cycle at module load.
        from .facebook_service import publish_facebook_post

        try:
            res = await publish_facebook_post(
                FacebookPublishInput(
                    image_url=post.image_url, caption=post.caption
                )
            )
            self._update(job_id, status="published", post_id=res.post_id)
            log.info("Scheduled job %s published", job_id)
        except SocialError as exc:
            self._update(job_id, status="failed",
                         error=f"{exc.code}: {exc.details or exc.message}")
            log.error("Scheduled job %s failed: %s", job_id, exc.details)
        except Exception as exc:  # noqa: BLE001 - must not escape the scheduler
            self._update(job_id, status="failed", error=repr(exc))
            log.exception("Scheduled job %s crashed", job_id)


scheduler_service = SchedulerService()
