from fastapi.testclient import TestClient
from backend.tests.test_auth import session_fixture, client_fixture, test_register_and_verify

def test_book_flow(client: TestClient):
    test_register_and_verify(client) # Creates t1@example.com
    r_login = client.post("/auth/login", json={"email":"t1@example.com","password":"p"})
    token = r_login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    r = client.post("/rides/book", headers=headers, json={
        "email": "t1@example.com",
        "pickup": "A", "drop": "B",
        "pickup_lat": 12.0, "pickup_lon": 77.0,
        "drop_lat": 12.1, "drop_lon": 77.1
    })
    assert r.status_code == 200
    assert "ride_id" in r.json()