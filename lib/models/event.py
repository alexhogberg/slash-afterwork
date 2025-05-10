from lib.models.event_place import EventPlace


class Event:
    """
    A class to represent an Event in the application.
    """

    def __init__(self, _id, team_id, date, time, location, description=None, participants=None, author=None):
        """
        Initialize an Event object.

        :param date: The date of the event.
        :param time: The time of the event.
        :param location: The location of the event.
        :param description: Optional description of the event.
        :param participants: Optional list of participants.
        :param author: Optional author of the event.
        """
        self._id = _id
        self.team_id = team_id
        self.date = date
        self.time = time
        self.location: EventPlace = location
        self.participants = participants if participants is not None else []
        self.author = author
        self.description = description

    def __str__(self):
        """
        Return a string representation of the Event.
        """
        return f"Event(id={self._id}, date={self.date}, time={self.time}, location={self.location}, description={self.description}, participants={self.participants}, author={self.author})"

    def to_dict(self):
        """
        Convert the Event object to a dictionary.
        """
        return {
            "_id": self._id,
            "date": self.date,
            "time": self.time,
            "location": self.location,
            "description": self.description,
            "participants": self.participants,
            "author": self.author,
        }

    @classmethod
    def from_dict(cls, data):
        """
        Create an Event object from a dictionary.

        :param data: A dictionary containing event details.
        :return: An Event object.
        """
        return cls(
            id=data.get("id"),
            date=data.get("date"),
            time=data.get("time"),
            location=data.get("location"),
            description=data.get("description"),
            participants=data.get("participants"),
            author=data.get("author"),
        )