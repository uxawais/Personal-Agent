import pytest
from channels.base import IncomingMessage, OutgoingMessage


def test_incoming_message():
    msg = IncomingMessage(
        channel="slack",
        user_id="U123",
        conversation_id="slack:C123:T456",
        content="Hello",
    )
    assert msg.channel == "slack"
    assert msg.content == "Hello"


def test_outgoing_message():
    msg = OutgoingMessage(
        channel="whatsapp",
        user_id="+1234567890",
        conversation_id="whatsapp:+1234567890",
        content="Hi there!",
    )
    assert msg.channel == "whatsapp"
    assert msg.content == "Hi there!"
