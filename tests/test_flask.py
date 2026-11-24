import pytest

from flask_app import app


@pytest.fixture
def client():
    app.config.update(TESTING=True)
    return app.test_client()


def test_form_and_greeting(client):
    assert client.get("/").status_code == 200
    response = client.post("/", data={"name": "  Александр  "})
    assert response.status_code == 200
    assert "Привет, Александр!" in response.get_data(as_text=True)


@pytest.mark.parametrize("data", [{}, {"name": "   "}, {"name": "x" * 51}])
def test_invalid_name(client, data):
    assert client.post("/", data=data).status_code == 400


def test_html_in_name_is_escaped(client):
    response = client.post("/", data={"name": "<script>alert(1)</script>"})
    html = response.get_data(as_text=True)
    assert "<script>alert(1)</script>" not in html
    assert "&lt;script&gt;" in html


def test_students_table(client):
    response = client.get("/students")
    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert "<table>" in html
    assert "Анна Иванова" in html
    assert "221341" in html
    assert html.count("<tr>") == 4
    assert client.get("/static/style.css").status_code == 200
