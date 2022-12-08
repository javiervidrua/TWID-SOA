from multimeta import MultipleMeta  # https://stackoverflow.com/a/49936625
import json


class Board(metaclass=MultipleMeta):
    def __init__(self):
        # Load all the data from the json file
        with open('twid.json', 'r') as file:
            self.twid = json.load(file)

        # Initialize everything
        self.round = 1
        self.score = [{'name': player, 'score': 0} for player in self.twid['players']]

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
        # If the player exists
        if player in self.twid['players']:
            # https://book.pythontips.com/en/latest/map_filter.html
            # Filter self.score with filter for the specified player
            # Then map the result so it looks like {'score': $score}

            # https://stackoverflow.com/questions/29563153/python-filter-function-single-result
            # And finally get the element of the iterator
            return next(map(lambda x: x['score'], filter(lambda x: x['name'] == player, self.score)), {})
        return {}

    def scorePlayerPut(self, player, score):
        # If the player exists and 0 <= score <= 100
        if player in self.twid['players'] and score >= 0 and score <= 100:
            for index, item in enumerate(self.score):
                if item['name'] == player:
                    self.score[index]['score'] = score
                    return score

        return False

    # Map methods
    def mapGet(self):
        return self.twid['regions']

    def mapRegionGet(self, region):
        return [{'country': country['name']} for country in self.twid['countries'] if country['region'] == region]
    
    def mapRegionPut(self, region, countries):
        # If the regions and all of the countries exist
        if region in self.twid['regions'] and set([country['country'] for country in countries]).issubset([country['name'] for country in self.twid['countries']]): # https://stackoverflow.com/questions/3931541/how-to-check-if-all-of-the-following-items-are-in-a-list
            for index, item in enumerate(self.twid['countries']):
                
                # Remove all the countries of the specified region
                if item['region'] == region:
                    self.twid['countries'][index]['region'] = ''
            
                # Add all the specified new countries of the specified region
                if item['name'] in [country['country'] for country in countries]:
                    self.twid['countries'][index]['region'] = region
            return True

        return False
    
    def mapRegionCountryGet(self, region, country):
        return next(({'stability': item['stability'], 'isConflictive': item['isConflictive'], 'isOilProducer': item['isOilProducer'], 'influence': item['influence']} for item in self.twid['countries'] if item['region'] == region and item['name'] == country), {}) # https://stackoverflow.com/questions/58380706/python-list-comprehension-filter-single-element-in-the-list
    
    def mapRegionCountryPut(self, region, country, newCountry):
        # If the regions and all of the countries exist
        if region in self.twid['regions'] and set([country]).issubset([country['name'] for country in self.twid['countries']]):
            for index, item in enumerate(self.twid['countries']):
                
                if item['name'] == country:
                    # If the stability and the influence have a valid value
                    if newCountry['stability'] in range(1, 5+1) and set(newCountry['influence'].values()).issubset(range(1, 100+1)):
                        self.twid['countries'][index].update(newCountry) # https://stackoverflow.com/questions/405489/python-update-object-from-dictionary
                        return True

        return False
