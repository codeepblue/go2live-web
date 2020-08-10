import math
import os
import re
from datetime import datetime
from math import ceil
from natsort import natsorted
from moviepy.editor import VideoFileClip

from flask import Flask, session, redirect, url_for, request, render_template, abort
from flask_socketio import SocketIO, emit, join_room, send, leave_room

from config import Configuration
from crypto import Crypto
from db import Database
from cache import Cache
from forms import LoginForm, CreateLiveForm, RegisterUserForm, UpdateLiveForm, AuthenticateWatcher
from log_setup import get_logger
from schema import User, generate_id, Live, generate_key, STATE_VOD, STATE_LIVE, STATE_NOT_STARTED

app = Flask(__name__)

# default configuration from environment
config = Configuration()

# logging
log = get_logger(config)

# database access
db = Database(config)

# crypto helper
crypto = Crypto(config)

# socket.io
socketio = SocketIO(app)

# cache
cache = Cache(config)

app.secret_key = config.app_session_key


@app.route("/", methods=["GET"])
def index():
    if "logged" in session:
        return redirect(url_for("dashboard"))
    return render_template("index.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    login_form = LoginForm()
    if request.method == "POST":
        if login_form.validate_on_submit():
            email = request.form["email"]
            password = crypto.hash(request.form["password"])
            with db.open_session() as db_session:
                user = db_session.query(User).filter(
                    User.email == email,
                    User.password == password).first()
            if user:
                session["logged"] = True
                session["user.id"] = user.id
                session["user.username"] = user.username
                session["user.email"] = user.email
                return redirect(url_for("dashboard"))
    return render_template("login.html", form=login_form)


# @app.route("/register", methods=["GET", "POST"])
# def register():
#     register_user_form = RegisterUserForm()
#     if register_user_form.validate_on_submit():
#         user = User()
#         register_user_form.populate_obj(user)
#         with db.open_session() as db_session:
#             user_email_exist = db_session.query(User.email).filter(User.email == user.email).count() > 0
#         if user_email_exist:
#             register_user_form.email.errors.append("Email already tacked")
#             return render_template("register.html", form=register_user_form)
#         user.id = generate_id()
#         user.created_at = datetime.now()
#         user.updated_at = datetime.now()
#         user.password = crypto.hash(user.password)
#         with db.open_session() as db_session:
#             db_session.add(user)
#
#         return redirect(url_for("login"))
#     return render_template("register.html", form=register_user_form)


@app.route("/logout", methods=["GET"])
def logout():
    if "logged" in session:
        session.pop("logged")
        session.pop("user.id")
        session.pop("user.username")
        session.pop("user.email")
    if "watcher.nickname" in session:
        session.pop("watcher.nickname")
    return redirect(url_for("login"))


@app.route("/dashboard", methods=["GET"])
def dashboard():
    if "logged" not in session:
        return redirect(url_for("login"))
    current_page = 0
    if "p" in request.args:
        current_page = int(request.args["p"])
    lives_per_page = 5
    with db.open_session() as db_session:
        lives = db_session\
            .query(Live)\
            .filter(
                Live.user_id == session["user.id"],
                Live.deleted_at == None,
            )\
            .order_by(Live.updated_at.desc())\
            .limit(lives_per_page)\
            .offset(current_page*lives_per_page)\
            .all()
        number_of_lives = db_session.query(Live).filter(Live.user_id == session["user.id"]).count()
    number_of_pages=ceil(number_of_lives/lives_per_page)-1
    for live in lives:
        if live.duration:
            minutes, seconds = divmod(live.duration, 60)
            if minutes:
                live.readable_duration = "{} minutos e {} segundos".format(minutes, seconds)
            else:
                live.readable_duration = "{} segundos".format(seconds)
    create_live_form = CreateLiveForm()
    username = session["user.username"]
    return render_template("dashboard.html", title="Dashboard", form=create_live_form, username=username,
                           lives=lives, current_page=current_page, number_of_pages=number_of_pages)


@app.route("/live", methods=["POST"])
def live():
    if "logged" not in session:
        return redirect(url_for("login"))
    create_live_form = CreateLiveForm()
    if create_live_form.validate_on_submit():
        live = Live()
        create_live_form.populate_obj(live)
        session["user.id"]
        live.id = generate_id()
        live.user_id = session["user.id"]
        live.state = STATE_NOT_STARTED
        live.duration = 0
        live.viewer_count = 0
        live.created_at = datetime.now()
        live.updated_at = datetime.now()
        with db.open_session() as db_session:
            stream_key = generate_key()
            while db_session.query(Live.stream_key).filter(Live.stream_key == stream_key).first():
                stream_key = generate_key()
            live.stream_key = stream_key
            watch_key = generate_key()
            while db_session.query(Live.watch_key).filter(Live.watch_key == watch_key).first():
                watch_key = generate_key()
            live.watch_key = watch_key
            db_session.add(live)

        return redirect(url_for("get_live", id=live.id))
    return redirect("dashboard", form=create_live_form)


@app.route("/live/<id>", methods=["GET"])
def get_live(id):
    if "logged" not in session:
        return redirect(url_for("login"))
    with db.open_session() as db_session:
        live = db_session.query(Live).filter(Live.id == id).first()
    if not live:
        return render_template("error.html", errors=["Live ou Vídeo não encontrado"], username=session["user.username"], next_url=url_for("dashboard"))

    ingest_url = config.ingest_destination
    embed_url = "{}embed/{}".format(request.url_root, live.watch_key)
    watch_source_url = config.watch_source(live)
    socket_io_url = config.socket_io_url
    update_live_form = UpdateLiveForm()
    return render_template("live.html", title=live.title, username=session["user.username"], form=update_live_form,
                           live=live, ingest_url=ingest_url, embed_url=embed_url, watch_source_url=watch_source_url,
                           socket_io_url=socket_io_url)


@app.route("/live/<id>", methods=["POST"])
def update_live(id):
    if "logged" not in session:
        return redirect(url_for("login"))
    with db.open_session() as db_session:
        live = db_session.query(Live).filter(Live.id == id).first()
    if not live:
        return render_template("error.html", errors=["Live ou Vídeo não encontrado"], username=session["user.username"], next_url=url_for("dashboard"))
    update_live_form = UpdateLiveForm()
    if update_live_form.validate_on_submit():
        update_live_form.populate_obj(live)
        live.updated_at = datetime.now()
        with db.open_session() as db_session:
            db_session.add(live)
        return redirect(url_for("get_live", id=live.id))
    return render_template("live.html", title=live.title, username=session["user.username"], form=update_live_form,
                           live=live)


@app.route("/live/<id>/delete", methods=["POST"])
def delete_live(id):
    if "logged" not in session:
        return redirect(url_for("login", next_url=url_for("get_live", id)))
    with db.open_session() as db_session:
        live = db_session.query(Live).filter(Live.id == id, Live.user_id == session["user.id"]).first()
        if not live or (live.user_id != session["user.id"]):
            return render_template("error.html", errors=["Live ou Vídeo não encontrado"], username=session["user.username"], next_url=url_for("dashboard"))
        live.deleted_at = datetime.now()
        db_session.add(live)
    return redirect(url_for("dashboard"))


def generate_vod(stream_key):
    vod_content = "#EXTM3U\n#EXT-X-VERSION:3\n#EXT-X-PLAYLIST-TYPE:VOD\n#EXT-X-TARGETDURATION:10\n"
    base_path = os.path.join(config.record_path, stream_key)
    files = natsorted([f for f in os.listdir(base_path) if f.endswith(".ts")])
    total_duration = 16.667 * len(files)
    for file in files:
        vod_content += "#EXTINF:{},\n{}\n".format(16.667, file)
    vod_file = os.path.join(config.record_path, stream_key, "vod.m3u8")
    vod_content += "#EXT-X-ENDLIST"
    with open(vod_file, "w+") as vod:
        vod.write(vod_content)
    return vod_file, total_duration


@app.route("/live/<id>/start", methods=["GET"])
def start_live(id):
    if "logged" not in session:
        return redirect(url_for("login", next_url=url_for("get_live", id)))
    with db.open_session() as db_session:
        live = db_session.query(Live).filter(Live.id == id, Live.user_id == session["user.id"]).first()
        live.state = STATE_LIVE
        live.updated_at = datetime.now()
        db_session.add(live)
    cache.set("live.stream_key.{}".format(live.stream_key))
    return redirect(url_for("get_live", id=id))


@app.route("/live/<id>/stop", methods=["POST"])
def stop_live(id):
    if "logged" not in session:
        return redirect(url_for("login", next_url=url_for("get_live", id)))
    with db.open_session() as db_session:
        live = db_session.query(Live).filter(Live.id == id, Live.user_id == session["user.id"]).first()
        if not live or (live.user_id != session["user.id"]):
            return render_template("error.html", errors=["Live ou Vídeo não encontrado"], username=session["user.username"], next_url=url_for("dashboard"))
        vod_file, vod_duration = generate_vod(live.stream_key)
        live.duration = math.ceil(vod_duration)
        live.state = STATE_VOD
        live.updated_at = datetime.now()
        db_session.add(live)
    return redirect(url_for("get_live", id=id))


@app.route("/watch/<watch_key>", methods=["GET", "POST"])
def watch(watch_key):
    username = "" if "user.username" not in session else session["user.username"]
    with db.open_session() as db_session:
        live = db_session.query(Live).filter(Live.watch_key == watch_key).first()
    if not live:
        return render_template("error.html", errors=["Live ou Vídeo não encontrado"], username=username, next_url=url_for("dashboard"))

    socket_io_url = config.socket_io_url
    watch_source_url = config.watch_source(live)

    # if live password is empty or user is logged and is owner, render watch page
    if ("watcher.nickname" in session) or ("logged" in session and "user.id" in session and live.user_id == session["user.id"]):
        username = session["watcher.nickname"] if "watcher.nickname" in session else session["user.username"]
        return render_template("watch.html", title=live.title, username=username,
                               live=live, watch_source_url=watch_source_url, socket_io_url=socket_io_url)

    # if user is not the owner or is not logged in, require live password
    authenticate_watcher_form = AuthenticateWatcher()
    if authenticate_watcher_form.validate_on_submit():
        if (live.password and authenticate_watcher_form.password.data == live.password) or (not live.password):
            session["watcher.nickname"] = authenticate_watcher_form.nickname.data
            with db.open_session() as db_session:
                live = db_session.query(Live).filter(Live.watch_key == watch_key).first()
                live.viewer_count += 1
                db_session.add(live)
            return redirect(url_for("watch", watch_key=watch_key))
        authenticate_watcher_form.password.errors.append("Senha inválida, tente novamente")

    live_has_password = False
    if live.password:
        live_has_password = True
    return render_template("viewer-login.html", form=authenticate_watcher_form, watch_key=watch_key, live_has_password=live_has_password )


@app.route("/embed/<watch_key>", methods=["GET"])
def embed(watch_key):
    with db.open_session() as db_session:
        live = db_session.query(Live).filter(Live.watch_key == watch_key).first()
    watch_source = config.watch_source(live)
    return render_template("embed.html", live=live, watch_source=watch_source)


@socketio.on("message", namespace="/chat")
def chat_message(message):
    log.info(message)

    data = message["data"]
    if not "room" in data:
        abort(400, "room not set")
    if not "nickname" in data:
        abort(400, "nickname not set")
    if not "text" in data:
        abort(400, "text not set")

    response = {
        "data": {
            "nickname": data["nickname"],
            "text": data["text"]
        }
    }
    emit('response', response, room=data["room"])


@socketio.on('join', namespace="/chat")
def on_join(data):
    log.info("join", data)
    username = data['nickname']
    room = data['room']
    join_room(room)


@socketio.on('leave', namespace="/chat")
def on_leave(data):
    username = data['nickname']
    log.info("user {} as leave".format(username))
    room = data['room']
    leave_room(room)
    emit("leave", {"data": "user"})
