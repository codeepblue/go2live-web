from contextlib import contextmanager
from uuid import uuid4

import pytest

from schema import Live
from api_routes import app
from config import Configuration
from db import Database

test_users = [
    ("test", "test@example.org", "test1234", True, True),
    ("user", "user@example.org", "user1234", False, True),
    ("invalid", "invalid", "invalid", False, False),
]

test_live_update_data = [
    ("foo", 0, True),
    ("foo", 1, True),
    ("foo", 7, True),
    ("foo", 15, True),
    ("foo", 30, True),
    ("", 0, True),
    ("", 1, True),
    ("", 7, True),
    ("", 15, True),
    ("", 30, True),
    ("i", 1, False),
    ("this-is-a-really-big-invalid-password", 1, False),
]

index_description_text = b"Lives privadas, anonimato"


@pytest.fixture(scope="session")
def client():
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    return app.test_client()


def wipe_db():
    db = Database(Configuration())
    db.wipe_db()
    return db


@contextmanager
def logged_user(client, email, password):
    client.post("/login", data=dict(
        email=email,
        password=password
    ), follow_redirects=True)
    yield
    client.get("/logout", follow_redirects=True)


@pytest.mark.parametrize("username,email,password,existing,valid", test_users)
def test_get_index(client, username, email, password, existing, valid):
    wipe_db()
    with logged_user(client, email, password):
        rv = client.get("/", follow_redirects=True)
        assert rv.content_type == "text/html; charset=utf-8"
        assert rv.status_code == 200
        if existing:
            assert b"Dashboard" in rv.data
        else:
            assert index_description_text in rv.data


@pytest.mark.parametrize("username,email,password,existing,valid", test_users)
def test_post_login(client, username, email, password, existing, valid):
    rv = client.post("/login", data=dict(
        email=email,
        password=password
    ), follow_redirects=True)
    if valid and existing:
        assert rv.content_type == "text/html; charset=utf-8"
        assert rv.status_code == 200
        assert b"Dashboard" in rv.data
    else:
        assert rv.content_type == "text/html; charset=utf-8"
        assert rv.status_code == 200
        assert b"Fazer Login" in rv.data


@pytest.mark.parametrize("username,email,password,existing,valid", test_users)
def test_post_register(request, client, username, email, password, existing, valid):
    wipe_db()
    request.addfinalizer(wipe_db)
    rv = client.post("/register", data=dict(
        username=username,
        email=email,
        password=password,
        confirm_password=password
    ), follow_redirects=True)
    assert rv.content_type == "text/html; charset=utf-8"
    assert rv.status_code == 200
    if not valid or existing:
        assert b"is-invalid" in rv.data
        assert b"Criar Conta" in rv.data
    if valid and not existing:
        assert not b"is-invalid" in rv.data
        assert b"Fazer Login" in rv.data


@pytest.mark.parametrize("username,email,password,existing,valid", test_users)
def test_get_logout(request, client, username, email, password, existing, valid):
    wipe_db()
    request.addfinalizer(wipe_db)
    rv = client.get("/logout", follow_redirects=True)
    if not existing:
        client.post("/register", data=dict(
            username=username,
            email=email,
            password=password,
            confirm_password=password
        ), follow_redirects=True)
    client.post("/login", data=dict(
        email=email,
        password=password
    ), follow_redirects=True)
    rv = client.get("/logout", follow_redirects=True)
    assert rv.content_type == "text/html; charset=utf-8"
    assert rv.status_code == 200
    assert b"Fazer Login" in rv.data


@pytest.mark.parametrize("username,email,password,existing,valid", test_users)
def test_post_live(request, client, username, email, password, existing, valid):
    wipe_db()
    request.addfinalizer(wipe_db)
    live_title = uuid4().hex
    with logged_user(client, email, password):
        rv = client.post("/live", data=dict(
            title=live_title,
        ), follow_redirects=True)
        if not existing:
            assert rv.content_type == "text/html; charset=utf-8"
            assert rv.status_code == 200
            assert b"Fazer Login" in rv.data
        elif existing:
            assert rv.content_type == "text/html; charset=utf-8"
            assert rv.status_code == 200
            assert live_title.encode("ascii") in rv.data


@pytest.mark.parametrize("username,email,password,existing,valid", test_users)
@pytest.mark.parametrize("live_password,live_expires_in,live_valid", test_live_update_data)
def test_post_live_configuration(request, client, username, email, password, existing, valid, live_password,
                                 live_expires_in, live_valid):
    db = wipe_db()
    request.addfinalizer(db.wipe_db)
    live_title = uuid4().hex
    with logged_user(client, email, password):
        rv = client.post("/live", data=dict(
            title=live_title,
        ), follow_redirects=True)
        if not existing:
            assert rv.content_type == "text/html; charset=utf-8"
            assert rv.status_code == 200
            assert b"Fazer Login" in rv.data
        elif existing:
            with db.open_session() as db_session:
                live = db_session.query(Live).filter(Live.title == live_title).one()
            rv = client.post("/live/" + live.id, data=dict(
                password=live_password,
                expires_in=live_expires_in,
            ), follow_redirects=True)
            if live_valid:
                assert rv.content_type == "text/html; charset=utf-8"
                assert rv.status_code == 200
                if live_expires_in:
                    days_label = "dias"
                    if live_expires_in == 1:
                        days_label = "dia"
                    assert '<option value="{0}" selected>{0} {1}</option>'.format(live_expires_in, days_label).encode(
                        "ascii") in rv.data
                else:
                    assert '<option value="" selected>Nāo expira</option>'
                assert '<input type="password" class="form-control" id="password" name="password" value="{}">'.format(
                    live_password).encode("ascii") in rv.data
            elif not live_valid:
                assert rv.content_type == "text/html; charset=utf-8"
                assert rv.status_code == 200
                assert b'is-invalid' in rv.data
                assert b'<div class="invalid-feedback">' in rv.data


@pytest.mark.parametrize("username,email,password,existing,valid", test_users)
def test_watch(request, client, username, email, password, existing, valid):
    db = wipe_db()
    request.addfinalizer(db.wipe_db)
    with db.open_session() as db_session:
        testing_live = db_session.query(Live).filter(Live.title == "Live de teste 1").first()
    with logged_user(client, email, password):
        rv = client.get("/watch?v=" + testing_live.watch_key, follow_redirects=True)
        assert rv.content_type == "text/html; charset=utf-8"
        assert rv.status_code == 200
        assert testing_live.title.encode("ascii") in rv.data
