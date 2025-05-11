import logging
import os

import google.maps.places_v1.types as place_types
from google.maps import places_v1

fieldMask = "places.displayName,places.formattedAddress,places.priceLevel,places.rating,places.types,places.id,places.current_opening_hours,places.icon_mask_base_uri,places.website_uri,places.photos,places.reviews,places.business_status"


class GooglePlaces:
    def __init__(self):
        self.logger = logging.getLogger()
        self.logger.setLevel(logging.INFO)
        self.gMaps = places_v1.PlacesClient(
            client_options={"api_key": os.environ["GOOGLE_PLACES_API_KEY"]},
        )

    def get_suggestions(self, area) -> list[place_types.Place]:
        suggestions = places_v1.SearchTextRequest(text_query=area, open_now=True)

        response = self.gMaps.search_text(
            request=suggestions, metadata=[("x-goog-fieldmask", fieldMask)]
        )
        if response:
            return response.places
        return []

    def get_place_information(self, place_id) -> place_types.Place:
        place = places_v1.GetPlaceRequest(
            name=f"places/{place_id}",
        )
        fieldMask = "*"
        return self.gMaps.get_place(
            request=place, metadata=[("x-goog-fieldmask", fieldMask)]
        )

    def get_place_suggestions(self, place_name) -> list[dict]:
        self.logger.info(place_name)
        suggestions = []
        places = places_v1.SearchTextRequest(text_query=place_name, open_now=True)

        places_result = self.gMaps.search_text(
            request=places, metadata=[("x-goog-fieldmask", fieldMask)]
        )

        for place in places_result.places:
            suggestions.append(
                {
                    "text": {
                        "type": "plain_text",
                        "text": place.display_name.text,
                    },
                    "description": {
                        "type": "plain_text",
                        "text": place.formatted_address,
                    },
                    "value": place.id,
                }
            )

        return suggestions

    def format_place(self, place: place_types.Place):
        return {
            "name": place.display_name.text,
            "address": place.formatted_address,
            "price_level": place.price_level,
            "rating": place.rating,
            "types": list(place.types),
            "place_id": place.id,
            "website_uri": place.website_uri,
            "business_status": place.business_status,
            "google_maps_url": place.google_maps_uri,
        }
