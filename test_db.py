from unittest import TestCase
from unittest.mock import patch, MagicMock

import sqlalchemy
from pytest import raises

from db import Database


class TestDatabaseTestCase(TestCase):
    def setUp(self) -> None:
        super().setUp()
        mock_config = MagicMock()
        mock_config.db_driver = "postgresql+psycopg2"
        mock_config.db_username = "username"
        mock_config.db_password = "password"
        mock_config.db_hostname = "hostname"
        mock_config.db_port = 123
        mock_config.db_name = "db_name"
        mock_config.app_name = "test"
        self.config = mock_config
        self.db = Database(self.config)

    def test_connection_string(self):
        self.assertEqual(self.db.connection_string(), "postgresql+psycopg2://username:password@hostname:123/db_name")

    @patch("sqlalchemy.create_engine", MagicMock())
    @patch("sqlalchemy.orm.sessionmaker", MagicMock())
    def test_get_session_without_existing_session(self):
        with self.db.open_session() as session:
            self.assertIsInstance(session, sqlalchemy.orm.session.Session)

    @patch("sqlalchemy.create_engine", MagicMock())
    @patch("sqlalchemy.orm.sessionmaker", MagicMock())
    def test_transactional_calls_commit_on_success(self):
        mocked_fn = MagicMock()
        mocked_session = MagicMock()
        with self.db.open_session(mocked_session) as session:
            mocked_fn()

        self.assertTrue(mocked_fn.called)
        self.assertTrue(mocked_session.commit.called)
        self.assertFalse(mocked_session.rollback.called)

    @patch("sqlalchemy.create_engine", MagicMock())
    @patch("sqlalchemy.orm.sessionmaker", MagicMock())
    def test_transactional_calls_rollback_on_fail(self):
        mocked_session = MagicMock()
        with raises(Exception):
            with self.db.open_session(mocked_session) as session:
                raise Exception
        self.assertFalse(mocked_session.commit.called)
        self.assertTrue(mocked_session.rollback.called)
