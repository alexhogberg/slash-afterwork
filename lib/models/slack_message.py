class SlackMessage:
    """
    A class to represent a Slack message as it is sent to the Slack API.
    """

    def __init__(self, text: str, channel: str = None, username: str = None, icon_emoji: str = None, blocks: list = []):
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
        self.blocks = blocks

    def to_dict(self) -> dict:
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