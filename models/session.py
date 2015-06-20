from google.appengine.ext import ndb
from protorpc import messages


class Session(ndb.Model):
    """Session -- Session object"""
    organizerUserId = ndb.StringProperty()
    name = ndb.StringProperty(required=True)
    highlights = ndb.StringProperty(repeated=True)
    speaker = ndb.StringProperty()
    duration = ndb.StringProperty()
    typeOfSession = ndb.StringProperty(repeated=True)
    date = ndb.DateProperty()
    startTime = ndb.IntegerProperty()
    conferenceKeyBelongTo = ndb.StringProperty()


class SessionForm(messages.Message):
    """SessionForm -- Session outbound form message"""
    organizerUserId = messages.StringField(1)
    name = messages.StringField(2)
    highlights = messages.StringField(3, repeated=True)
    speaker = messages.StringField(4)
    duration = messages.StringField(5)
    typeOfSession = messages.EnumField('TypeOfSession', 6, repeated=True)
    date = messages.StringField(7)
    startTime = messages.StringField(8)
    organizerDisplayName = messages.StringField(9)


class SessionForms(messages.Message):
    """SessionForms -- multiple Session outbound form message"""
    items = messages.MessageField(SessionForm, 1, repeated=True)


class SessionQueryForm(messages.Message):
    """SessionQueryForm -- Session query inbound form message"""
    field = messages.StringField(1)
    operator = messages.StringField(2)
    value = messages.StringField(3)


class SessionQueryForms(messages.Message):
    """SessionQueryForms -- multiple SessionQueryForm inbound form message"""
    filters = messages.MessageField(SessionQueryForm, 1, repeated=True)


class TypeOfSession(messages.Enum):
    """TypeOfSession -- session type enumeration value"""
    NOT_SPECIFIED = 1
    LECTURE = 2
    KEYNOTE = 3
    WORKSHOP = 4
    DEMO = 5
    SOCIAL = 6


class FeaturedSpeaker(messages.Message):
    """FeaturedSpeaker -- Featured speaker info. outbound message"""
    speaker = messages.StringField(1)
    sessionNames = messages.StringField(2, repeated=True)


class FeaturedSpeakerList(messages.Message):
    """FeaturedSpeakerList
        -- multiple  Featured speaker info. outbound message"""
    items = messages.MessageField(FeaturedSpeaker, 1, repeated=True)
