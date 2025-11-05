from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.database import create_db_and_tables, engine, get_session
from sqlmodel import SQLModel, Session
import pytest

# --- Fixtures (No Change) ---

@pytest.fixture(name="session")
def session_fixture():
    SQLModel.metadata.drop_all(engine)
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session

@pytest.fixture(name="client")
def client_fixture(session: Session):
    def get_session_override():
        return session
    app.dependency_overrides[get_session] = get_session_override
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()

# --- Helper Function (No Change) ---

def test_register_and_verify(client: TestClient):
    r = client.post("/auth/register", json={"name":"t1","email":"t1@example.com","password":"p","role":"passenger"})
    assert r.status_code == 200
    
    r2 = client.post("/auth/verify_otp", json={"email":"t1@example.com","otp":"123456"})
    assert r2.status_code == 200
    assert r2.json()["message"] == "User verified successfully"

# --- Test Cases (Updated with new tests) ---

def test_login_success(client: TestClient):
    # This is a "happy path" test
    test_register_and_verify(client)
    r = client.post("/auth/login", json={"email":"t1@example.com","password":"p"})
    assert r.status_code == 200
    assert "access_token" in r.json()

# (UPDATED) - EXAMPLE OF A FAILURE-PATH TEST
def test_login_wrong_password(client: TestClient):
    # This tests a failure scenario, which is crucial for coverage
    test_register_and_verify(client) # Creates user "t1@example.com"
    r = client.post("/auth/login", json={"email":"t1@example.com","password":"wrong_password"})
    
    # We expect a 401 Unauthorized error
    assert r.status_code == 401
    assert r.json()["detail"] == "Invalid credentials"

# (UPDATED) - EXAMPLE OF A FAILURE-PATH TEST
def test_login_user_not_found(client: TestClient):
    # This tests another failure scenario
    r = client.post("/auth/login", json={"email":"nouser@example.com","password":"p"})
    
    # We expect a 401 Unauthorized error
    assert r.status_code == 401
    assert r.json()["detail"] == "Invalid credentials"

# (UPDATED) - EXAMPLE OF A FAILURE-PATH TEST
def test_verify_otp_invalid(client: TestClient):
    # Register, but don't verify
    client.post("/auth/register", json={"name":"t2","email":"t2@example.com","password":"p","role":"passenger"})
    
    # Send the wrong OTP
    r = client.post("/auth/verify_otp", json={"email":"t2@example.com","otp":"000000"})
    
    assert r.status_code == 400
    assert r.json()["detail"] == "Invalid OTP"

def test_failed_login_lockout(client: TestClient):
    test_register_and_verify(client)
    for _ in range(5):
        r = client.post("/auth/login", json={"email":"t1@example.com","password":"wrong"})
        assert r.status_code == 401
    
    # 6th attempt should fail and account should be locked
    r_lock = client.post("/auth/login", json={"email":"t1@example.com","password":"p"})
    assert r_lock.status_code == 403 # 403 Forbidden (account not active)

# (UPDATED) ---
# TODO: YOU MUST ADD MORE TESTS HERE
# - test_register_email_already_exists
# - test_verify_otp_expired
# - test_login_with_otp_success
# - test_login_with_otp_fail
# - ... and so on for every function