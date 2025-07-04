def login(client, username):
    return client.post("/login", data={"username": username, "password": "secret"})


def test_weather_endpoint(client, test_user, monkeypatch):
    login(client, test_user.username)

    async def fake_fetch(lat, lon):
        return {
            "name": "Lima",
            "main": {"temp": 21},
            "weather": [{"description": "clear", "icon": "01d"}],
        }

    monkeypatch.setattr("crunevo.routes.dashboard_routes.fetch_weather", fake_fetch)
    resp = client.get("/dashboard/weather?lat=0&lon=0")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["city"] == "Lima"
    assert data["temp"] == 21
