from dataclasses import dataclass
from datetime import datetime, timezone
import os

from infrai_client import infrai


@dataclass(frozen=True)
class CreatorRecord:
    message_id: str
    creator_id: str
    object_keys: list[str]
    stale_after: datetime


def stale(record: CreatorRecord, now: datetime) -> bool:
    return record.stale_after <= now


def process_once(bucket: str, queue: str, now: datetime | None = None) -> int:
    now = now or datetime.now(timezone.utc)
    messages = infrai.queue.consume(queue=queue, max_messages=50, visibility_timeout=60).get("messages", [])
    removed = 0
    for message in messages:
        payload = message.get("payload", {})
        record = CreatorRecord(message["message_id"], payload["creator_id"],
                               payload.get("object_keys", []), datetime.fromisoformat(payload["stale_after"]))
        if stale(record, now):
            infrai.storage.object.delete_batch(bucket, keys=record.object_keys)
            removed += 1
        infrai.queue.ack(queue=queue, message_id=record.message_id)
    return removed


def register_sweep(task_url: str) -> str:
    job = infrai.cron.create(cron_expr="0 2 * * *", task=task_url)
    return job["job_id"]


def ensure_setup(queue: str, bucket: str) -> None:
    infrai.queue.create(name=queue)
    infrai.storage.bucket.create(name=bucket)


if __name__ == "__main__":
    queue = os.environ.get("CREATOR_QUEUE", "creator-cleanup")
    bucket = os.environ.get("CREATOR_BUCKET", "creator-assets")
    ensure_setup(queue, bucket)
    print({"removed": process_once(bucket, queue)})
