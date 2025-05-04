import os
import pytest
from dotenv import load_dotenv
from lib.api.google_places import GooglePlaces
from google.maps import places_v1

# Load environment variables from .env file
load_dotenv()

@pytest.fixture
def google_places():
    """
    Fixture to initialize the GooglePlaces class.
    """
    return GooglePlaces()

def test_get_suggestions_valid_area(google_places):
    """
    Test the get_suggestions method with a valid area.
    """
    area = "bars near rådmansgatan"
    suggestions = google_places.get_suggestions(area)
    assert suggestions, "No suggestions returned"
    assert len(suggestions) > 0, "No places found in suggestions"
    for suggestion in suggestions:
        assert suggestion.display_name.text, "Place name is missing"
        assert suggestion.formatted_address, "Place address is missing"
        assert suggestion.rating is not None, "Place rating is missing"

def test_get_suggestions_invalid_area(google_places):
    """
    Test the get_suggestions method with an invalid area.
    """
    area = "nonexistentplace12345"
    suggestions = google_places.get_suggestions(area)
    assert len(suggestions) == 0, "Suggestions should be empty for an invalid area"

def test_get_place_information(google_places):
    """
    Test the get_place_information method with a valid place ID.
    """
    # Use a known valid place ID for testing
    valid_place_id = "ChIJN1t_tDeuEmsRUsoyG83frY4"  # Example Google Place ID
    place = google_places.get_place_information(valid_place_id)
    assert place.name, "Place name is missing"
    assert place.formatted_address, "Place address is missing"
    assert place.rating is not None, "Place rating is missing"

def test_get_place_information_invalid_id(google_places):
    """
    Test the get_place_information method with an invalid place ID.
    """
    invalid_place_id = "invalid_place_id_12345"
    with pytest.raises(Exception):
        google_places.get_place_information(invalid_place_id)

def test_get_place_suggestions(google_places):
    """
    Test the get_place_suggestions method with a valid place name.
    """
    place_name = "bars near rådmansgatan"
    suggestions = google_places.get_place_suggestions(place_name)
    assert suggestions, "No suggestions returned"
    assert len(suggestions) > 0, "No suggestions found"
    for suggestion in suggestions:
        assert suggestion['text']['text'], "Suggestion text is missing"
        assert suggestion['value'], "Suggestion value (place ID) is missing"