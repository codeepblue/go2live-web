import json
from contextlib import contextmanager
from datetime import datetime

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, close_all_sessions
from sqlalchemy.pool import NullPool

from log_setup import get_logger
from crypto import Crypto
from schema import Base, generate_id, User, generate_key, Live, STATE_LIVE, STATE_NOT_STARTED


class Database(object):
    engine = None
    session = None

    def __init__(self, config):
        self.migrated = False
        self.config = config
        self.logger = get_logger(config)

    # TODO create separated migrations file
    def migrate_database(self):
        self.logger.debug("started database migration")
        engine = self._get_engine()
        Base.metadata.create_all(engine)
        crypto = Crypto(self.config)
        # check if it was initialized
        with self.open_session() as session:
            if session.query(User).count():
                return
        # administrator user
        admin = User()
        admin.id = generate_id()
        admin.username = "Admin User"
        admin.email = "admin@example.org"
        admin.created_at = datetime.now()
        admin.updated_at = datetime.now()
        admin.password = crypto.hash("admin1234")
        # test user
        test = User()
        test.id = generate_id()
        test.username = "Test User"
        test.email = "test@example.org"
        test.created_at = datetime.now()
        test.updated_at = datetime.now()
        test.password = crypto.hash("test1234")
        # testing lives
        testing_lives = []
        for i in range(100):
            live = Live()
            live.id = generate_id()
            live.user_id = test.id
            live.title = "Live de teste {}".format(i)
            live.stream_key = generate_key()
            live.watch_key = generate_key()
            live.state = STATE_NOT_STARTED
            live.duration = 0
            live.viewer_count = 0
            live.created_at = datetime.now()
            live.updated_at = datetime.now()
            testing_lives.append(live)
        with self.open_session() as session:
            session.add(admin)
            session.add(test)
            session.add_all(testing_lives)
        self.logger.debug("finished database migration")

    def connection_string(self):
        return "{}://{}:{}@{}:{}/{}".format(
            self.config.db_driver,
            self.config.db_username,
            self.config.db_password,
            self.config.db_hostname,
            self.config.db_port,
            self.config.db_name
        )

    # TODO move to separate testing only file
    def wipe_db(self):
        self.logger.debug("recreating database")
        assert self.config.db_name == 'testing'
        close_all_sessions()
        engine = self._get_engine()
        Base.metadata.drop_all(engine)
        self.migrate_database()
        self.logger.debug("database recreated")

    def _get_engine(self):
        if self.engine:
            return self.engine
        self.engine = create_engine(self.connection_string(),
                                    poolclass=NullPool,
                                    json_serializer=json.dumps)
        self.migrate_database()
        return self.engine

    @contextmanager
    def open_session(self, session=None):
        if not session:
            Session = sessionmaker(bind=self._get_engine(), expire_on_commit=False)
            session = Session()
        try:
            yield session
            session.commit()
        except:
            session.rollback()
            raise
        finally:
            session.close()
