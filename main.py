#!/usr/bin/env python
from api_routes import socketio, app

if __name__ == '__main__':
    socketio.run(app, host="0.0.0.0")
