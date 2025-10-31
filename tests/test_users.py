import pytest
from fastapi.testclient import TestClient
from app.main import app, get_db
from app.models import Base, UserDB, ProjectDB
from app.database import engine, SessionLocal
import uuid

# ---------- Database Setup ----------
Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)
TestingSessionLocal = SessionLocal


# ---------- Fixtures ----------
@pytest.fixture
def db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

@pytest.fixture
def client(db):
    def override_get_db():
        try:
            yield db
        finally:
            db.close()
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c

@pytest.fixture
def test_user(db):
    sid = f"S{str(uuid.uuid4().int)[:7]}"
    email = f"alice_{uuid.uuid4().hex[:6]}@example.com"
    user = UserDB(name="Alice", email=email, age=23, student_id=sid)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

@pytest.fixture
def test_project(db, test_user):
    project = ProjectDB(name="Proj1", description="Initial", owner_id=test_user.id)
    db.add(project)
    db.commit()
    db.refresh(project)
    return project


# ---------- Tests ----------
def test_create_user(client):
    unique = str(uuid.uuid4().int)[:7]
    r = client.post(
        "/api/users",
        json={"name": "Paul", "email": f"pl_{unique}@atu.ie", "age": 25, "student_id": f"S{unique}"},
    )
    assert r.status_code == 201, r.text
    assert r.json()["name"] == "Paul"

def test_put_user(client, test_user):
    unique = str(uuid.uuid4().int)[:7]
    data = {"name": "Updated", "email": f"new_{unique}@example.com", "age": 30, "student_id": f"S{unique}"}
    res = client.put(f"/api/users/{test_user.id}", json=data)
    assert res.status_code == 200, res.text
    assert res.json()["name"] == "Updated"

def test_patch_user(client, test_user):
    new_email = f"patched_{uuid.uuid4().hex[:6]}@example.com"
    data = {"email": new_email}
    res = client.patch(f"/api/users/{test_user.id}", json=data)
    assert res.status_code == 200, res.text
    assert res.json()["email"] == new_email

def test_put_project(client, test_project, test_user):
    data = {"name": "Replaced Project", "description": "New desc", "owner_id": test_user.id}
    res = client.put(f"/api/projects/{test_project.id}", json=data)
    assert res.status_code == 200, res.text
    assert res.json()["name"] == "Replaced Project"

def test_patch_project(client, test_project):
    data = {"description": "Partially updated"}
    res = client.patch(f"/api/projects/{test_project.id}", json=data)
    assert res.status_code == 200, res.text
    assert res.json()["description"] == "Partially updated"
