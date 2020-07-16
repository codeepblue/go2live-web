from config import Configuration
import redis

DEFAULT_EXPIRE = 2 * 60  # 2 hours


class Cache(object):
    def __init__(self, config: Configuration):
        self.client = redis.Redis(
            host=config.redis_host,
            port=config.redis_port,
            db=config.redis_db,
            socket_keepalive=True,
            health_check_interval=10,
            client_name=config.app_name)

    def set(self, key: str, value=1, ttl=DEFAULT_EXPIRE):
        self.client.set(key, value, ex=ttl)

    def get(self, key: str):
        return self.client.get(key)