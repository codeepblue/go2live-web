from flask import Flask, request, make_response

from . import operations
from .schema import Event

app = Flask(__name__)


@app.route('/publish', methods=["POST"])
@app.route('/play', methods=["POST"])
@app.route('/done', methods=["POST"])
@app.route('/record_done', methods=["POST"])
def on_events():
    form = request.form
    app.logger.debug("New request with data {}".format(form))
    stream_key = form.get("name")
    if not operations.stream_key_exists(app, stream_key):
        app.logger.debug("Stream key {} not found".format(stream_key))
        return make_response("Invalid request", 401)
    try:
        app.logger.debug("Loading event data")
        event = Event(form)
        app.logger.debug("Saving event {}".format(event.__dict__))
        operations.save_event(app, event)
        app.logger.debug("Saved event {}".format(event.__dict__))
    except Exception as e:
        app.logger.exception(e)

    app.logger.debug("Stream key {} found, allowing stream".format(stream_key))
    return make_response("OK", 200)


@app.errorhandler(Exception)
def handle_exception(e):
    app.logger.exception(e)
    return make_response("Something bad happen", 500)
