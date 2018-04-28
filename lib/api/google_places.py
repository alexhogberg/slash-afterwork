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
