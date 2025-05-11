import pytest
from lib.models.slack_message import SlackMessage

def test_slack_message_initialization():
    message = SlackMessage(
        text="Hello, world!",
        channel="#general",
        username="Bot",
        icon_emoji=":robot_face:",
        blocks=[{"type": "section", "text": {"type": "mrkdwn", "text": "Hello, world!"}}]
    )
    assert message.text == "Hello, world!"
    assert message.channel == "#general"
    assert message.username == "Bot"
    assert message.icon_emoji == ":robot_face:"
    assert len(message.blocks) == 1

def test_slack_message_to_dict():
    message = SlackMessage(text="Hello, world!", channel="#general")
    message_dict = message.to_dict()
    assert message_dict["channel"] == "#general"
    assert message_dict["text"] == "Hello, world!"
    assert "blocks" not in message_dict

def test_add_block():
    message = SlackMessage(text="Hello, world!")
    block = {"type": "section", "text": {"type": "mrkdwn", "text": "Block text"}}
    message.add_block(block)
    assert len(message.blocks) == 1
    assert message.blocks[0] == block

def test_add_section_block():
    message = SlackMessage(text="Hello, world!")
    message.add_section_block("Section text", fields=["Field 1", "Field 2"])
    assert len(message.blocks) == 1
    assert message.blocks[0]["type"] == "section"
    assert message.blocks[0]["text"]["text"] == "Section text"
    assert len(message.blocks[0]["fields"]) == 2

def test_add_divider_block():
    message = SlackMessage(text="Hello, world!")
    message.add_divider_block()
    assert len(message.blocks) == 1
    assert message.blocks[0]["type"] == "divider"

def test_add_action_block():
    message = SlackMessage(text="Hello, world!")
    elements = [{"type": "button", "text": {"type": "plain_text", "text": "Click me"}}]
    message.add_action_block(elements)
    assert len(message.blocks) == 1
    assert message.blocks[0]["type"] == "actions"
    assert message.blocks[0]["elements"] == elements

def test_add_context_block():
    message = SlackMessage(text="Hello, world!")
    elements = [{"type": "mrkdwn", "text": "Context text"}]
    message.add_context_block(elements)
    assert len(message.blocks) == 1
    assert message.blocks[0]["type"] == "context"
    assert message.blocks[0]["elements"] == elements

def test_clear_blocks():
    message = SlackMessage(text="Hello, world!")
    message.add_section_block("Section text")
    message.add_divider_block()
    assert len(message.blocks) == 2
    message.clear_blocks()
    assert len(message.blocks) == 0