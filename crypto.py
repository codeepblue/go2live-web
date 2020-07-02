import hashlib


class Crypto(object):
    def __init__(self, config):
        self.config = config

    def hash(self, string):
        salt = self.config.app_password_salt
        hasher = hashlib.sha256()
        hasher.update(salt.encode("utf-8") + string.encode("utf-8"))
        return hasher.hexdigest()
