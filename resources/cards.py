from multimeta import MultipleMeta # https://stackoverflow.com/a/49936625

class Cards(metaclass=MultipleMeta):
    def __init__(self):
        pass

    def __repr__(self):
        return str([
            {'name': 'deck'},
            {'name': 'playing'},
            {'name': 'player'}
        ])
