# coding=utf-8
class Place:
    def __init__(self, place):
        self.gMapsPlace = place

    def name(self):
        return self.gMapsPlace['name']

    def rating(self):
        if 'rating' in self.gMapsPlace:
            return self.gMapsPlace['rating']
        return 'Not rated'

    def isOpen(self):
        if 'opening_hours' in self.gMapsPlace:
            return True if self.gMapsPlace['opening_hours'].get('open_now', None) else False
        return None

    def address(self):
        return self.gMapsPlace.get('formatted_address', 'Location Unknown')

    def url(self):
        return self.gMapsPlace.get('url')

    def format_field(self, title, text):
        return {"title": title, "value": text, 'short': 1}

    def format_open(self):
        if self.isOpen():
            return {'color': 'good', 'text': 'Open'}
        elif self.isOpen() is None:
            return {'color': '#cccccc', 'text': 'Unknown'}
        return {'color': 'danger', 'text': 'Closed'}

    def image_url(self):
        return self.gMapsPlace.get('icon')


    def format_action(self):
        return {
            'name': 'afterwork',
            'text': 'Create afterwork',
            'type': 'button',
            'value': self.gMapsPlace['place_id']
        }

    def format_attachment(self, add_actions=True):
        attachment = {
            'author_name': "{name} ({availability})".format(name=self.name(), availability=self.format_open()['text']),
            'author_link': self.url(),
            'callback_id': 'create_afterwork',
            'color': self.format_open()['color'],
            'fields': [
                self.format_field('Rating', self.rating()),
                self.format_field('Address', self.address())
            ],
            'author_icon': self.image_url()
        }

        if add_actions:
            attachment['actions'] = [
                self.format_action()
            ]

        return attachment

