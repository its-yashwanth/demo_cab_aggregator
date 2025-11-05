from fastapi.testclient import TestClient
from sqlmodel import Session
from backend.app.models import User
from backend.app.utils.hashing import hash_password
from backend.tests.test_auth import session_fixture, client_fixture

def test_admin_access_denied(client: TestClient, session: Session):
    # Create passenger
    client.post("/auth/register", json={"name":"p1","email":"p1@example.com","password":"p"})
    client.post("/auth/verify_otp", json={"email":"p1@example.com","otp":"123456"})
    r_login = client.post("/auth/login", json={"email":"p1@example.com","password":"p"})
    token = r_login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    r_admin = client.get("/admin/reports", headers=headers)
    assert r_admin.status_code == 403 # Forbidden

def test_admin_access_granted(client: TestClient, session: Session):
    # Create admin manually
    admin_user = User(
        name="admin", 
        email="admin@example.com", 
        password=hash_password("adminpass"), 
        role="admin", 
        is_active=True
    )
    session.add(admin_user)
    session.commit()
    
    r_login = client.post("/auth/login", json={"email":"admin@example.com","password":"adminpass"})
    assert r_login.status_code == 200
    token = r_login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    r_admin = client.get("/admin/reports", headers=headers)
    assert r_admin.status_code == 200
    assert "total_rides" in r_admin.json()