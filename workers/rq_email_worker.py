import os
import sys

# Make sure that the project root is in Python's path
PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..")
)
sys.path.insert(0, PROJECT_ROOT)

from dotenv import load_dotenv
import redis
from rq import Worker, Queue

# Load .env (works on PythonAnywhere - if cwd is correct)
load_dotenv()

REDIS_URL = os.getenv("REDIS_CONNECTION_URL")

if not REDIS_URL:
    raise RuntimeError("REDIS_CONNECTION_URL not set")

listen = ["emails_high", "emails_low"]

redis_conn = redis.from_url(REDIS_URL)

if __name__ == "__main__":
    queues = [Queue(name, connection=redis_conn) for name in listen]
    worker = Worker(
        queues,
        connection=redis_conn,
        name="rm-stock-tracker-rq-email-worker",
    )
    worker.work()