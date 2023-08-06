import redis
from rq import Worker, Queue, Connection
import os

os.environ["OBJC_DISABLE_INITIALIZE_FORK_SAFETY"] = "YES"

listen = ["default"]

redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")

conn = redis.from_url(redis_url)

from rq.job import Job

if __name__ == "__main__":
    with Connection(conn):
        worker = Worker(map(Queue, listen), job_class=Job)
        worker.work()
