import pytest
from fastapi.testclient import TestClient

from lab6.api import create_app

STUDENT = {"name": "Александр Мовчан", "age": 20, "group_name": "221341"}


@pytest.fixture
def client(tmp_path):
    with TestClient(create_app(tmp_path / "students.sqlite3")) as client:
        yield client


def test_json_endpoint(client):
    response = client.get("/api/info")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/json")
    assert response.json()["variant"] == 2
    assert response.json()["lab"] == 6
    assert client.get("/").json() == response.json()


def test_crud(client):
    assert client.get("/api/students").json() == []
    response = client.post("/api/students", json=STUDENT)
    assert response.status_code == 201
    student = response.json()
    student_id = student["id"]
    assert student == {"id": student_id, **STUDENT}
    url = f"/api/students/{student_id}"
    assert client.get(url).json() == student
    assert client.get("/api/students").json() == [student]
    updated = {**STUDENT, "age": 21}
    response = client.put(url, json=updated)
    assert response.status_code == 200
    assert response.json() == {"id": student_id, **updated}
    assert client.get(url).json()["age"] == 21
    response = client.delete(url)
    assert response.status_code == 204
    assert response.content == b""
    assert client.get(url).status_code == 404
    assert client.get("/api/students").json() == []


def test_missing_student(client):
    assert client.get("/api/students/999").status_code == 404
    assert client.put("/api/students/999", json=STUDENT).status_code == 404
    assert client.delete("/api/students/999").status_code == 404


@pytest.mark.parametrize(
    "changes",
    [
        {"name": "   "},
        {"name": "x" * 101},
        {"group_name": ""},
        {"age": 0},
        {"age": 121},
        {"age": "twenty"},
        {"age": True},
        {"unexpected": 1},
    ],
)
def test_invalid_student(client, changes):
    response = client.post("/api/students", json={**STUDENT, **changes})
    assert response.status_code == 422
    assert client.get("/api/students").json() == []


def test_parameterized_sql_and_trimming(client):
    name = "Robert'); DROP TABLE students;--"
    data = {**STUDENT, "name": f"  {name}  "}
    response = client.post("/api/students", json=data)
    assert response.status_code == 201
    assert response.json()["name"] == name
    assert client.get("/api/students").json()[0]["name"] == name
    assert client.post("/api/students", json=STUDENT).status_code == 201


def test_database_survives_restart(tmp_path):
    path = tmp_path / "nested" / "students.sqlite3"
    with TestClient(create_app(path)) as first:
        student = first.post("/api/students", json=STUDENT).json()
    with TestClient(create_app(path)) as second:
        assert second.get("/api/students").json() == [student]


def test_chat_page_and_api_docs(client):
    assert client.get("/chat").status_code == 200
    assert client.get("/static/chat.js").status_code == 200
    assert client.get("/docs").status_code == 200
    assert "/api/students" in client.get("/openapi.json").json()["paths"]
