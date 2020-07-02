from datetime import datetime

import pytest
import sqlalchemy
from sqlalchemy.orm import session

from config import Configuration
from db import Database
from schema import Ping, generate_id


@pytest.fixture
def db():
    db = Database(Configuration())
    db.wipe_db()
    return db


def test_connection_string(db):
    assert db.connection_string() == "postgresql+psycopg2://web:secret@db:5432/testing"


def test_get_session_without_existing_session(db):
    with db.open_session() as session:
        assert isinstance(session, sqlalchemy.orm.session.Session)


def test_session_can_select(db):
    with db.open_session() as session:
        session.execute("SELECT 1").scalar() == 1


def test_session_can_create_table(db):
    with db.open_session() as session:
        session.execute("CREATE TABLE IF NOT EXISTS test (id int, name varchar(255), age int)")
    with db.open_session() as session:
        result = session.execute("INSERT INTO test (id, name, age) VALUES (1, 'foo', 2)")
        assert result.rowcount == 1
        session.execute("DROP TABLE IF EXISTS test")


def test_session_can_insert_entity(db):
    ping = Ping()
    ping.id = generate_id()
    ping.created_at = datetime.now()
    ping.updated_at = datetime.now()
    with db.open_session() as session:
        session.add(ping)
    with db.open_session() as session:
        assert session.query(Ping).count() == 1


def test_transaction_can_insert_entity(db):
    ping = Ping()
    ping.id = generate_id()
    ping.created_at = datetime.now()
    ping.updated_at = datetime.now()
    with db.open_session() as session:
        session.add(ping)
    with db.open_session() as session:
        assert session.query(Ping).count() == 1


def test_transaction_can_update_entity(db):
    ping = Ping()
    ping.id = generate_id()
    ping.created_at = datetime.now()
    ping.updated_at = datetime.now()
    with db.open_session() as session:
        session.add(ping)
    with db.open_session() as session:
        ping2 = session.query(Ping).get(ping.id)
        ping2.created_at = datetime.now()
        ping2.updated_at = datetime.now()
        session.add(ping2)
    with db.open_session() as session:
        ping3 = session.query(Ping).get(ping2.id)
    assert ping3.created_at == ping2.created_at
