import pytest
from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

from lab6.api import create_app


@pytest.fixture
def client(tmp_path):
    with TestClient(create_app(tmp_path / "students.sqlite3")) as client:
        yield client


def test_broadcast_and_disconnect(client):
    with client.websocket_connect("/ws/chat?name=Alice") as alice:
        assert alice.receive_json()["type"] == "system"
        with client.websocket_connect("/ws/chat?name=Bob") as bob:
            assert bob.receive_json()["type"] == "system"
            alice.send_text("Привет!")
            message = alice.receive_json()
            assert message["name"] == "Alice"
            assert message["text"] == "Привет!"
            assert bob.receive_json() == message
            bob.send_text("Ответ")
            message = bob.receive_json()
            assert message["name"] == "Bob"
            assert alice.receive_json() == message
        alice.send_text("После выхода Bob")
        assert alice.receive_json()["text"] == "После выхода Bob"
    assert not client.app.state.chat.connections


def test_invalid_messages_and_recovery(client):
    with client.websocket_connect("/ws/chat?name=Alice") as ws:
        ws.receive_json()
        for message in ["   ", "x" * 1001]:
            ws.send_text(message)
            assert ws.receive_json()["type"] == "error"
        ws.send_bytes(b"binary")
        assert ws.receive_json()["type"] == "error"
        ws.send_text("  Всё работает  ")
        assert ws.receive_json()["text"] == "Всё работает"


@pytest.mark.parametrize("name", ["", "%20%20", "x" * 51])
def test_invalid_chat_name(client, name):
    with pytest.raises(WebSocketDisconnect) as exc:
        with client.websocket_connect(f"/ws/chat?name={name}"):
            pass
    assert exc.value.code == 1008
