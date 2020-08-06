import os
import redis
import json
from time import time

redis_client = None

LIVE_STREAM_KEY = "live.stream_key.{}"
LIVE_EVENT = "live.{}.events.{}"


def client(app):
    global redis_client
    if redis_client is not None:
        return redis_client
    REDIS_HOST = os.getenv("REDIS_HOST")
    REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
    REDIS_DB = int(os.getenv("REDIS_DB", "0"))
    app.logger.debug("Connecting to REDIS {}:{}/{}".format(REDIS_HOST, REDIS_PORT, REDIS_DB))
    redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB)
    return redis_client


def stream_key_exists(app, stream_key):
    if stream_key is None:
        return False
    key = LIVE_STREAM_KEY.format(stream_key)
    app.logger.debug("Looking for stream key {}".format(key))
    result = client(app).get(key)
    if result is None:
        return False
    app.logger.debug("Stream key {} found".format(stream_key))
    return result


def save_event(app, event):
    if event is None:
        return
    event_id = LIVE_EVENT.format(event.stream_key, int(time()))
    data = json.dumps(event.__dict__)
    client(app).set(event_id, data)
    app.logger.debug("Created new event {}".format(event_id))
