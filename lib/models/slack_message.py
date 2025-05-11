class SlackMessage:
    """
    A class to represent a Slack message as it is sent to the Slack API.
    """

    def __init__(self, text: str, channel: str = None, username: str = None, icon_emoji: str = None, blocks: list = None):
        """
        Initialize a SlackMessage instance.

        :param channel: The Slack channel ID or name to send the message to.
        :param text: Optional. The plain text of the message.
        :param username: Optional. The username to display as the sender.
        :param icon_emoji: Optional. The emoji to use as the sender's icon.
        :param blocks: Optional. A list of block elements for rich formatting.
        """
        self.channel = channel
        self.text = text
        self.username = username
        self.icon_emoji = icon_emoji
        self.blocks = blocks if blocks is not None else []

    def to_dict_say(self) -> dict:
        """
        Convert the SlackMessage instance to a dictionary suitable for the Slack API.

        :return: A dictionary representation of the Slack message.
        """
        message = {
            "channel": self.channel,
        }
        if self.text:
            message["text"] = self.text
        if self.username:
            message["username"] = self.username
        if self.icon_emoji:
            message["icon_emoji"] = self.icon_emoji
        if self.blocks:
            message["blocks"] = self.blocks
        return message

    def to_dict_respond(self) -> dict:
        """
        Convert the SlackMessage instance to a dictionary suitable for the Slack API.

        :return: A dictionary representation of the Slack message.
        """
        message = {}
        if self.text:
            message["text"] = self.text
        if self.blocks:
            message["blocks"] = self.blocks
        return message

    def add_block(self, block: dict):
        """
        Add a block to the message.

        :param block: A dictionary representing a Slack block.
        """
        self.blocks.append(block)

    def add_section_block(self, text: str, fields: list = None):
        """
        Add a section block to the message.

        :param text: The main text of the section block.
        :param fields: Optional. A list of fields for the section block.
        """
        block = {
            "type": "section",
            "text": {"type": "mrkdwn", "text": text},
        }
        if fields:
            block["fields"] = [{"type": "mrkdwn", "text": field} for field in fields]
        self.add_block(block)

    def add_divider_block(self):
        """
        Add a divider block to the message.
        """
        self.add_block({"type": "divider"})

    def add_action_block(self, elements: list):
        """
        Add an action block to the message.

        :param elements: A list of action elements (e.g., buttons).
        """
        self.add_block({"type": "actions", "elements": elements})

    def add_context_block(self, elements: list):
        """
        Add a context block to the message.

        :param elements: A list of context elements (e.g., images or text objects).
        """
        block = {
            "type": "context",
            "elements": elements,
        }
        self.add_block(block)

    def clear_blocks(self):
        """
        Clear all blocks from the message.
        """
        self.blocks = []