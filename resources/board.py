from multimeta import MultipleMeta # https://stackoverflow.com/a/49936625

class Board(metaclass=MultipleMeta):
    def __init__(self):
        pass

    def __repr__(self):
        return str([
            {'name': 'round'},
            {'name': 'score'},
            {'name': 'map'},
            {'name': 'nwo'}
        ])
