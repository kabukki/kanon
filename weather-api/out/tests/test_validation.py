def test_missing_location_is_400(client):
    r = client.get("/weather/current")
    assert r.status_code == 400


def test_both_city_and_coords_is_400(client):
    r = client.get("/weather/current", params={"city": "Paris", "lat": 48.85, "lng": 2.35})
    assert r.status_code == 400


def test_partial_coords_is_400(client):
    r = client.get("/weather/current", params={"lat": 48.85})
    assert r.status_code == 400


def test_out_of_range_lat_is_422(client):
    r = client.get("/weather/current", params={"lat": 999, "lng": 0})
    assert r.status_code == 422
