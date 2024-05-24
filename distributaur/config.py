# distributaur/config.py

from distributaur.utils import get_env_vars


class Config:
    def __init__(self):
        self.settings = {}
        self.settings.update(get_env_vars())

    def configure(self, **kwargs):
        self.settings.update(kwargs)

    def get(self, key, default=None):
        return self.settings.get(key, default)

config = Config()
