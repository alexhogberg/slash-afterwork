# coding=utf-8


from google.maps.places_v1.types import Place


class EventPlace:
    def __init__(self, place):
        self.gMapsPlace: Place = place

    def name(self):
        return self.gMapsPlace.display_name.text

    def rating(self):
        if 'rating' in self.gMapsPlace:
            return self.gMapsPlace.rating
        return 'Not rated'

    def isOpen(self):
        return True if self.gMapsPlace.current_opening_hours.open_now else False

    def opening_hours(self):
        if self.gMapsPlace.current_opening_hours:
            return ', '.join(self.gMapsPlace.current_opening_hours.weekday_descriptions)
        elif self.gMapsPlace.regular_opening_hours:
            return ', '.join(self.gMapsPlace.regular_opening_hours.weekday_descriptions)
        return None

    def address(self):
        return self.gMapsPlace.formatted_address

    def url(self):
        return self.gMapsPlace.website_uri

    def format_field(self, title, text):
        return {"title": title, "value": text, 'short': 1}

    def format_open(self):
        if self.isOpen():
            return {'color': 'good', 'text': 'Open'}
        elif self.isOpen() is None:
            return {'color': '#cccccc', 'text': 'Unknown'}
        return {'color': 'danger', 'text': 'Closed'}

    def image_url(self):
        return self.gMapsPlace.icon_mask_base_uri

    def format_block(self):
        block = [
            {
                "type": "header",
                        "text": {
                            "type": "plain_text",
                            "text": f"{self.name()} ({self.format_open()['text']})",
                            "emoji": True
                        }
            },
            {
                "type": "divider"
            },
            {
                "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": self.opening_hours()
                        }
            },
            {
                "type": "section",
                        "fields": [
                            {
                                "type": "mrkdwn",
                                "text": f"*Address*\n{self.address()}"
                            },
                            {
                                "type": "mrkdwn",
                                "text": f"*Rating*\n{self.rating()}"
                            },
                            {
                                "type": "mrkdwn",
                                "text": f"<{self.gMapsPlace.website_uri}|Website>"
                            }
                        ]
            },
            {
                "type": "divider"
            },
            {
                "type": "actions",
                        "elements": [
                            {
                                "type": "button",
                                "text": {
                                        "type": "plain_text",
                                        "text": "Create event",
                                                "emoji": True
                                },
                                "value": self.gMapsPlace.id,
                                "action_id": "create_event_suggest"
                            }
                        ]
            }
        ]
        
        return block
