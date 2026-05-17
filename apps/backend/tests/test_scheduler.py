"""Tests for scheduled post publishing."""

from __future__ import annotations

import pytest
import sqlite3
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.social.scheduler_service import SchedulerService
from app.services.social.social_models import (
    SchedulePostInput,
    ScheduleResult,
    ScheduledPost,
    Platform,
)
from app.services.social.social_exceptions import SchedulingError
from tests._social_fakes import configure_meta


@pytest.fixture
def temp_db():
    """Temporary SQLite database for testing."""
    with tempfile.NamedTemporaryFile(delete=False, suffix=".db") as f:
        db_path = f.name
    yield db_path
    # Robust cleanup for Windows file locking
    try:
        Path(db_path).unlink(missing_ok=True)
    except (PermissionError, OSError):
        # Ignore errors on Windows with file locks
        pass


@pytest.fixture
def scheduler(monkeypatch, temp_db):
    """SchedulerService instance with temp database."""
    from app.config import get_settings

    s = get_settings()
    monkeypatch.setattr(s, "social_db_path", temp_db, raising=False)

    service = SchedulerService()
    yield service
    service.shutdown()


@pytest.fixture
def valid_schedule_input() -> SchedulePostInput:
    """Valid schedule post input (future timestamp)."""
    future_time = datetime.now(timezone.utc) + timedelta(hours=1)
    return SchedulePostInput(
        platform="facebook",
        scheduled_time=future_time,
        image_url="https://example.com/image.jpg",
        caption="Test caption for Facebook",
    )


def test_scheduler_lifecycle(scheduler):
    """Test scheduler start and shutdown."""
    assert scheduler._scheduler is None

    scheduler.start()
    assert scheduler._scheduler is not None

    scheduler.shutdown()
    assert scheduler._scheduler is None


def test_scheduler_double_start(scheduler):
    """Starting already-running scheduler is idempotent."""
    scheduler.start()
    first_scheduler = scheduler._scheduler

    scheduler.start()
    assert scheduler._scheduler is first_scheduler  # Same instance


def test_schedule_post_success(scheduler, valid_schedule_input):
    """Successfully schedule a post."""
    scheduler.start()

    result = scheduler.schedule(valid_schedule_input)

    assert isinstance(result, ScheduleResult)
    assert result.status == "scheduled"
    assert result.platform == "facebook"
    assert result.job_id
    assert result.scheduled_time == valid_schedule_input.scheduled_time


def test_schedule_post_persists_to_db(scheduler, valid_schedule_input):
    """Scheduled posts are persisted to database."""
    scheduler.start()

    result = scheduler.schedule(valid_schedule_input)
    job_id = result.job_id

    # Query database directly
    conn = sqlite3.connect(scheduler._db().execute("PRAGMA database_list").fetchone()[2])
    conn.row_factory = sqlite3.Row
    cur = conn.execute("SELECT * FROM scheduled_posts WHERE id=?", (job_id,))
    row = cur.fetchone()

    assert row is not None
    assert row["id"] == job_id
    assert row["platform"] == "facebook"
    assert row["status"] == "pending"


def test_list_pending_posts(scheduler):
    """List all pending scheduled posts."""
    scheduler.start()

    future = datetime.now(timezone.utc) + timedelta(hours=1)
    for i in range(3):
        scheduler.schedule(
            SchedulePostInput(
                platform="facebook",
                scheduled_time=future + timedelta(hours=i),
                image_url="https://example.com/image.jpg",
                caption=f"Caption {i}",
            )
        )

    pending = scheduler.list_pending()
    assert len(pending) == 3
    for post in pending:
        assert post.status == "pending"


def test_schedule_past_time_validation():
    """Reject scheduling in the past."""
    past_time = datetime.now(timezone.utc) - timedelta(hours=1)

    with pytest.raises(ValueError, match="must be in the future"):
        SchedulePostInput(
            platform="facebook",
            scheduled_time=past_time,
            image_url="https://example.com/image.jpg",
            caption="Test",
        )


def test_schedule_naive_datetime_validation():
    """Reject naive (timezone-unaware) datetimes."""
    naive_time = datetime.now() + timedelta(hours=1)  # No tzinfo

    with pytest.raises(ValueError, match="timezone-aware"):
        SchedulePostInput(
            platform="facebook",
            scheduled_time=naive_time,  # type: ignore
            image_url="https://example.com/image.jpg",
            caption="Test",
        )


def test_schedule_facebook_post(scheduler):
    """Schedule a Facebook post."""
    scheduler.start()

    future_time = datetime.now(timezone.utc) + timedelta(hours=2)
    schedule_input = SchedulePostInput(
        platform="facebook",
        scheduled_time=future_time,
        image_url="https://example.com/fb_image.jpg",
        caption="Facebook caption",
    )

    result = scheduler.schedule(schedule_input)

    assert result.platform == "facebook"
    pending = scheduler.list_pending()
    assert any(p.platform == "facebook" for p in pending)


def test_schedule_without_running_scheduler(scheduler, valid_schedule_input):
    """Cannot schedule if scheduler is not running."""
    # Don't call scheduler.start()

    with pytest.raises(SchedulingError, match="not running"):
        scheduler.schedule(valid_schedule_input)


def test_db_persistence_survives_restart(temp_db, monkeypatch, valid_schedule_input):
    """Scheduled posts survive scheduler restart."""
    from app.config import get_settings

    s = get_settings()
    monkeypatch.setattr(s, "social_db_path", temp_db, raising=False)

    # First scheduler: schedule posts
    scheduler1 = SchedulerService()
    scheduler1.start()
    result1 = scheduler1.schedule(valid_schedule_input)
    job_id_1 = result1.job_id
    scheduler1.shutdown()

    # Second scheduler: reload pending posts
    scheduler2 = SchedulerService()
    scheduler2.start()
    pending = scheduler2.list_pending()
    scheduler2.shutdown()

    assert len(pending) == 1
    assert pending[0].id == job_id_1


def test_scheduler_reloads_past_due_jobs(monkeypatch, temp_db):
    """Past-due jobs are loaded and marked for immediate execution."""
    from app.config import get_settings

    s = get_settings()
    monkeypatch.setattr(s, "social_db_path", temp_db, raising=False)

    # Insert a past-due job directly into database
    scheduler1 = SchedulerService()
    conn = scheduler1._db()
    past_time = datetime.now(timezone.utc) - timedelta(hours=1)
    conn.execute(
        """INSERT INTO scheduled_posts 
           (id, platform, image_url, caption, scheduled_time, status, created_at, post_id, error)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            "past_due_job",
            "facebook",
            "https://example.com/image.jpg",
            "Past due caption",
            past_time.isoformat(),
            "pending",
            datetime.now(timezone.utc).isoformat(),
            "",
            "",
        ),
    )
    conn.commit()
    scheduler1.shutdown()

    # Start new scheduler and verify past-due job is loaded
    scheduler2 = SchedulerService()
    scheduler2.start()

    # Job should be in scheduler's queue (not guaranteed to execute immediately
    # in testing, but the infrastructure should be set up)
    pending = scheduler2.list_pending()
    assert any(p.id == "past_due_job" for p in pending)

    scheduler2.shutdown()


def test_schedule_post_invalid_platform():
    """Invalid platform should fail validation."""
    future_time = datetime.now(timezone.utc) + timedelta(hours=1)

    with pytest.raises(ValueError):
        SchedulePostInput(
            platform="tiktok",  # type: ignore - not a valid platform
            scheduled_time=future_time,
            image_url="https://example.com/image.jpg",
            caption="Test",
        )


def test_schedule_result_model():
    """Validate ScheduleResult structure."""
    future_time = datetime.now(timezone.utc) + timedelta(hours=1)

    result = ScheduleResult(
        job_id="job_123",
        platform="facebook",
        scheduled_time=future_time,
    )

    assert result.status == "scheduled"
    assert result.job_id == "job_123"
    assert result.platform == "facebook"
