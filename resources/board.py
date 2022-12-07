from multimeta import MultipleMeta  # https://stackoverflow.com/a/49936625


class Board(metaclass=MultipleMeta):
    def __init__(self):
        self.round = 1
        self.score = [
            {'name': 'US', 'score': 0},
            {'name': 'EU', 'score': 0},
            {'name': 'Russia', 'score': 0},
            {'name': 'China', 'score': 0},
        ]

    def __repr__(self):
        return str([
            {'name': 'round'},
            {'name': 'score'},
            {'name': 'map'},
            {'name': 'nwo'}
        ])

    # Round methods
    def roundGet(self):
        return self.round

    def roundAdd(self):
        if self.round < 8:
            self.round += 1
            return True
        return False

    def roundReset(self):
        self.round = 1

    # Score methods
    def scoreGet(self):
        return self.score

    def scorePlayerGet(self, player):
        if player in ['US', 'EU', 'Russia', 'China']:
            # https://book.pythontips.com/en/latest/map_filter.html
            # Filter self.score with filter
            # Then map the result

            # https://stackoverflow.com/questions/29563153/python-filter-function-single-result
            # And finally get the element of the iterator
            return next(map(lambda x: {'score': x['score']}, filter(lambda x: x['name'] == player, self.score)), {})
        return {}

    def scorePlayerPut(self, player, score):
        if player in ['US', 'EU', 'Russia', 'China'] and score >= 0 and score <= 100:
            for index, item in enumerate(self.score):
                if item['name'] == player:
                    self.score[index]['score'] = score
                    return {'score': score}

        return False
