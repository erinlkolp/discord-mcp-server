import pytest


@pytest.fixture
def sample_channels():
    return [
        {"id": "100", "name": "general", "type": 0, "topic": "General chat", "parent_id": "10"},
        {"id": "101", "name": "random", "type": 0, "topic": None, "parent_id": "10"},
        {"id": "102", "name": "Voice Chat", "type": 2, "topic": None, "parent_id": "10"},
        {"id": "10", "name": "Text Channels", "type": 4, "topic": None, "parent_id": None},
    ]


@pytest.fixture
def sample_messages():
    return [
        {
            "id": "msg1",
            "author": {"id": "u1", "username": "alice"},
            "content": "Hello!",
            "timestamp": "2026-03-15T10:00:00+00:00",
        },
        {
            "id": "msg2",
            "author": {"id": "u2", "username": "bob"},
            "content": "Hi there!",
            "timestamp": "2026-03-15T10:01:00+00:00",
        },
    ]


@pytest.fixture
def sample_send_response():
    return {
        "id": "msg999",
        "timestamp": "2026-03-15T12:00:00+00:00",
    }
