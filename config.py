import os

from schema import STATE_LIVE

ENV_PRODUCTION = "prod"


class Configuration(object):
    @staticmethod
    def _load(key):
        return os.environ[key]

    @property
    def db_driver(self):
        return "postgresql+psycopg2"

    @property
    def db_username(self):
        return self._load("DB_USERNAME")

    @property
    def db_password(self):
        return self._load("DB_PASSWORD")

    @property
    def db_hostname(self):
        return self._load("DB_HOSTNAME")

    @property
    def db_port(self):
        return 5432

    @property
    def db_name(self):
        return self._load("DB_NAME")

    @property
    def is_production(self):
        return self._load("APP_ENV") == ENV_PRODUCTION

    @property
    def is_development(self):
        return self._load("APP_ENV") != ENV_PRODUCTION

    @property
    def app_name(self):
        return self._load("APP_NAME")

    @property
    def app_session_key(self):
        return self._load("APP_SESSION_KEY")

    @property
    def app_password_key(self):
        return self._load("APP_PASSWORD_KEY")

    @property
    def app_password_salt(self):
        return self._load("APP_PASSWORD_SALT")

    def watch_source(self, live):
        if live.state == STATE_LIVE:
            m3u8_file = "index"
        else:
            m3u8_file = "vod"
        return "{}/{}/{}.m3u8".format(self._load("WATCH_SOURCE_SERVER"), live.stream_key, m3u8_file)

    @property
    def ingest_destination(self):
        return self._load("INGEST_DESTINATION_SERVER")

    @property
    def record_path(self):
        return self._load("APP_RECORD_PATH")

    @property
    def socket_io_url(self):
        return self._load("SOCKET_IO_SERVER")

    @property
    def redis_host(self):
        return "redis"

    @property
    def redis_port(self):
        return 6379

    @property
    def redis_db(self):
        return 0