import config
import requests
from multimeta import MultipleMeta # https://stackoverflow.com/a/49936625
from shortuuid import ShortUUID


class Game(metaclass=MultipleMeta):
    def __init__(self):
        response = requests.post(f'http://{config.ENV_URL_SERVICE_RESOURCES}/game')
        self.id = response.json()['id']
    
    def __repr__(self):
        return self.id
