from datetime import datetime, timezone, timedelta
from sweep_creator import CreatorRecord, stale


def test_stale_creator_is_selected_for_cleanup():
    now = datetime(2026, 1, 2, tzinfo=timezone.utc)
    old = CreatorRecord("m-1", "creator-7", ["a.zip"], now - timedelta(days=1))
    fresh = CreatorRecord("m-2", "creator-8", [], now + timedelta(days=1))
    assert stale(old, now) is True
    assert stale(fresh, now) is False
