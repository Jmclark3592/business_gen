from unittest.mock import Mock, patch
import pytest

from maps.geocode import *

@patch("requests.get")
def test_geocode_location_success(mock_get):
    mock_response = Mock()
    mock_response.json.return_value = {
        "status": "OK",
        "results": [
            {
                "geometry": {
                    "location": {
                        "lat": 123.456,
                        "lng": -78.901
                    }
                }
            }
        ]
    }
    mock_get.return_value = mock_response
    location = "Some Location"
    result = geocode_location(location)
    assert result == (123.456, -78.901)


@patch("requests.get")
def test_geocode_location_error(mock_get):
    mock_response = Mock()
    mock_response.json.return_value = {
        "status": "INVALID_REQUEST"
    }
    mock_get.return_value = mock_response
    location = "Invalid Location"
    with pytest.raises(ValueError) as context:
        geocode_location(location)
    assert str(context.value) == "Error geocoding location Invalid Location. Error message: INVALID_REQUEST"


def test_subdivide_region():
    min_lat = 0
    max_lat = 10
    min_lng = -10
    max_lng = 0
    num_divisions = 2

    result = subdivide_region(min_lat, max_lat, min_lng, max_lng, num_divisions)

    expected = [
        (0.0, 5.0, -10.0, -5.0),
        (0.0, 5.0, -5.0, 0.0),
        (5.0, 10.0, -10.0, -5.0),
        (5.0, 10.0, -5.0, 0.0)
    ]

    assert result == expected

@patch("requests.get")
def test_get_places_for_grid(mock_get):
    mock_response = Mock()
    mock_response.json.return_value = {
        "results": [
            {
                "name": "Place A",
                "place_id": "123"
            },
            {
                "name": "Place B",
                "place_id": "456"
            }
        ]
    }
    mock_get.return_value = mock_response
    query = "restaurant"
    min_lat, max_lat, min_lng, max_lng = 0, 1, -1, 0

    result = get_places_for_grid(query, min_lat, max_lat, min_lng, max_lng)

    expected = [
        {"name": "Place A", "place_id": "123"},
        {"name": "Place B", "place_id": "456"}
    ]

    assert result == expected

@patch("requests.get")
def test_get_place_details(mock_get):
    mock_response = Mock()
    mock_response.json.return_value = {
        "result": {
            "name": "Place A",
            "address": "123 Main St",
            "formatted_phone_number": "555-1234"  # Updated to match the Google Maps API key
        }
    }
    mock_get.return_value = mock_response
    place_id = "123456"

    result = get_place_details(place_id)

    expected = {
        "name": "Place A",
        "address": "123 Main St",
        "formatted_phone_number": "555-1234"  # Added phone number to expected result
    }

    assert result == expected


@patch("maps.geocode.subdivide_region")
@patch("maps.geocode.get_places_for_grid")
@patch("maps.geocode.get_place_details")
def test_get_places(mock_get_place_details, mock_get_places_for_grid, mock_subdivide_region):
    mock_subdivide_region.return_value = [
        (0, 1, -1, 0),
        (1, 2, -1, 0)
    ]
    mock_get_places_for_grid.side_effect = [
        [
            {"name": "Place A", "place_id": "123"},
            {"name": "Place B", "place_id": "456"}
        ],
        [
            {"name": "Place C", "place_id": "789"}
        ]
    ]
    mock_get_place_details.side_effect = [
        {"address": "123 Main St", "formatted_phone_number": "555-1234"},  # Added phone number
        {"address": "456 Elm St", "formatted_phone_number": "555-5678"},  # Added phone number
        {"address": "789 Oak St", "formatted_phone_number": "555-9101"}   # Added phone number
    ]

    query = "restaurant"
    min_lat, max_lat, min_lng, max_lng = 0, 2, -1, 0

    result = get_places(query, min_lat, max_lat, min_lng, max_lng)

    expected = [
        {"name": "Place A", "place_id": "123", "address": "123 Main St", "formatted_phone_number": "555-1234"},
        {"name": "Place B", "place_id": "456", "address": "456 Elm St", "formatted_phone_number": "555-5678"},
        {"name": "Place C", "place_id": "789", "address": "789 Oak St", "formatted_phone_number": "555-9101"}
    ]

    assert result == expected