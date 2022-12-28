import config
import requests
from multimeta import MultipleMeta  # https://stackoverflow.com/a/49936625
from shortuuid import ShortUUID


class Game(metaclass=MultipleMeta):
    def __init__(self):
        response = requests.post(f'http://{config.ENV_URL_SERVICE_RESOURCES}/game')
        self.id = response.json()['id']
        self.players = {'US': None, 'EU': None, 'Russia': None, 'China': None}
        self.isStarted = False
        self.isFinished = False

    def __repr__(self):
        return self.id

    def get_isStarted(self):
        return self.isStarted

    def get_isFinished(self):
        return self.isFinished

    def get_players(self):
        return self.players

    def set_player_user(self, player, user):
        if player in self.players:
            self.players[player] = user
            return True
        return False

    def start(self):
        self.isStarted = True

    def finish(self):
        self.isFinished = True
