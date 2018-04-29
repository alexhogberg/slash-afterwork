import logging
import os

import googlemaps

from lib.models.place import Place


class GooglePlaces:
    def __init__(self):
        self.logger = logging.getLogger()
        self.logger.setLevel(logging.INFO)
        self.gMaps = googlemaps.Client(key=os.environ['googleMapsApiKey'])

    def get_suggestions(self, area):
        suggestions = self.gMaps.places(
            query=area,
            type='bar',
            open_now=True
        )

        return suggestions

    def get_place_information(self, place_id):
        place = self.gMaps.place(
            place_id=place_id
        )
        return Place(place['result'])

    def get_place_suggestions(self, place_name):
        self.logger.info(place_name)
        suggestions = {
            'options': []
        }

        try:
            places = self.gMaps.places(
                query=place_name,
                type='bar'
            )

            self.logger.info(places)

            for place in places['results']:
                suggestions['options'].append({
                    'label': place['name'],
                    'value': place['place_id']
                })

            return suggestions
        except:
            raise



