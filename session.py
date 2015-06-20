import json
from datetime import datetime
from itertools import ifilter

import endpoints
from google.appengine.api import memcache
from google.appengine.ext import ndb
from protorpc import messages
from protorpc import message_types
from protorpc import remote

from core import EMAIL_SCOPE, API_EXPLORER_CLIENT_ID,\
    SESSION_FIELDS, OPERATORS, OPERATOR_LOOKUP
from models import BooleanMessage, ConflictException
from models.profile import Profile
from models.session import Session, SessionForm, SessionForms,\
    SessionQueryForms, TypeOfSession, FeaturedSpeakerList, FeaturedSpeaker

from settings import WEB_CLIENT_ID
from utils import getProfileFromUser
from utils import getUserId


# - - - - Request messages - - - - - - - - - - - - - - - - - - -

# Attributes:
#     - SessionForm: Session inbound form data
#     - websafeConferenceKey: Conference Key (web safe encoded)
# Usage:
#     - create a session entity with a given info.
SESSION_POST_REQUEST = endpoints.ResourceContainer(
    SessionForm,
    websafeConferenceKey=messages.StringField(1),
)

# Attributes:
#     - websafeConferenceKey: Conference Key (web safe encoded)
# Usage:
#     - Get all sessions' info. in the given conference
SESSION_GET_REQUEST = endpoints.ResourceContainer(
    message_types.VoidMessage,
    websafeConferenceKey=messages.StringField(1),
)

# Attributes:
#     - speaker: Speaker's name to search for sessions
# Usage:
#     - Get all sessions which the given speaker belong to
SESSION_GET_BY_SPEAKER_REQUEST = endpoints.ResourceContainer(
    message_types.VoidMessage,
    speaker=messages.StringField(1),
)

# Attributes:
#     - typeOfSession: Type of session
#         one of [NOT_SPECIFIED, LECTURE, KEYNOTE, WORKSHOP, DEMO, SOCIAL]
#     - websafeConferenceKey: Conference Key (web safe encoded)
# Usage:
#     - Get all sessions which contain the given typeOfSession.
SESSION_GET_BY_TYPE_REQUEST = endpoints.ResourceContainer(
    message_types.VoidMessage,
    typeOfSession=messages.StringField(1),
    websafeConferenceKey=messages.StringField(2),
)

# Attributes:
#     - websafeSessionKey: Session Key (web safe encoded)
# Usage:
#     - Allows a user to add the given session to their wishlist
SESSION_POST_WISHLIST_REQUEST = endpoints.ResourceContainer(
    message_types.VoidMessage,
    websafeSessionKey=messages.StringField(1),
)


@endpoints.api(name='sessions',
               version='v1',
               allowed_client_ids=[WEB_CLIENT_ID, API_EXPLORER_CLIENT_ID],
               scopes=[EMAIL_SCOPE])
class SessionApi(remote.Service):
    """Session API v0.1
    This class is of conference api. This class is consist of
    endpoint methods and helper methods.

    Attributes:
        @endpoints
            - getConferenceSessions(websafeConferenceKey):
                retrieve all sessions of the given conference key
                    and return it as a response
            - getConferenceSessionsByType(websafeConferenceKey,
                typeOfSession):
                retrieve all sessions which are of the given type
                    in the given conference
            - getSessionsBySpeaker():
                return all sessions given by the particular speaker,
                    across all conferences
            - createSession(websafeConferenceKey):
                create a new session in the given conference
                    with ```request.fields``` and return the result
                If a session with the speaker already exist,
                    append the speaker and the list of their sessions
                    to memcache with this key: "featured_speakers"
                See also: _cacheSession(speaker, confKey)
            - addSessionToWishlist(websafeSessionKey):
                a current user add the given conference in their wishlist
            - getSessionsInWishlist():
                get all the sessions that the user has added to their wishlist
            - querySessions(): query sessions with a form which is consist of
                field operator, and value.
                Example:
                    START_TIME < 02 15 PM and TYPE_OF_SESSION != WORKSHOP
            - getFeaturedSpeaker():
                get featured speakers who have more than one session
                    in a given conference
                    and list of their sessions' names
                retrieve data from memcache with this key: "featured_speakers"
                See also: _cacheSession(speaker, confKey)

        helper:
            _copySessionToForm(session):
                convert data(session) from database into Session form message
            _createSessionObject(request):
                convert data from inbound from message,
                    so it fits in Session model.
                Create a new session entity
            _cacheSession(speaker, confKey):
            _getQuery(request):
                retrieve data from database using formatted filters.
                See also: _formatFilters
            _formatFilters(filters):
                Format multiple filters into a list of python dictionary.
                The method _getQuery takes this return list.
                Use _lambaFilter to do in-memory filtering
                See also: _lambaFilter
            _lambaFilter(x, filter):
                x is from
                    ```ifilter(lambda x: _lambaFilter(x, filter), sessions)```
                Provide a lamba function for list filtering
            _convertTimeToInt(timeData):
                Convert Time object(hour, minute, AM/PM) to integer,
                    so it can be compared to other time column in database
            _recoverIntToTime(timeInteger):
                Recover Time object(hour, minute, AM/PM)
                    from integer in database,
                    so it fits in Session outbound form message
    """

    # - - - - API endpoints - - - - - - - - - - - - - - - - - - - - - - - - - -
    @endpoints.method(SESSION_GET_REQUEST, SessionForms,
                      path='conference/{websafeConferenceKey}/session',
                      http_method='GET', name='getConferenceSessions')
    def getConferenceSessions(self, request):
        # Given a conference, return all sessions
        c_key = ndb.Key(urlsafe=request.websafeConferenceKey)
        q = Session.query()
        sessions = q.filter(Session.conferenceKeyBelongTo == c_key.urlsafe())
        return SessionForms(
            items=[self._copySessionToForm(sf)
                   for sf in sessions]
        )

    @endpoints.method(SESSION_GET_BY_TYPE_REQUEST, SessionForms,
                      path='conference/{websafeConferenceKey}/'
                           'session/{typeOfSession}',
                      http_method='GET', name='getConferenceSessionsByType')
    def getConferenceSessionsByType(self, request):
        # Given a conference, return all sessions
        #     of a specified type (eg lecture, keynote, workshop)
        c_key = ndb.Key(urlsafe=request.websafeConferenceKey)
        q = Session.query()
        q = q.filter(Session.conferenceKeyBelongTo == c_key.urlsafe())
        sessions = q.filter(Session.typeOfSession == request.typeOfSession)
        return SessionForms(
            items=[self._copySessionToForm(sf)
                   for sf in sessions]
        )

    @endpoints.method(SESSION_GET_BY_SPEAKER_REQUEST, SessionForms,
                      path='session/{speaker}',
                      http_method='GET', name='getSessionsBySpeaker')
    def getSessionsBySpeaker(self, request):
        # Given a speaker, return all sessions given
        #     by this particular speaker, across all conferences
        q = Session.query()
        sessions = q.filter(Session.speaker == request.speaker)
        return SessionForms(
            items=[self._copySessionToForm(sf)
                   for sf in sessions]
        )

    @endpoints.method(SESSION_POST_REQUEST, SessionForm,
                      path='conference/{websafeConferenceKey}/session',
                      http_method='POST', name='createSession')
    def createSession(self, request):
        # Create a session object from form data and save it to database
        # Return a session object created
        # See also: _createSessionObject
        return self._createSessionObject(request)

    @endpoints.method(SESSION_POST_WISHLIST_REQUEST, BooleanMessage,
                      path='wishlist/session/{websafeSessionKey}',
                      http_method='POST', name='addSessionToWishlist')
    def addSessionToWishlist(self, request):
        # Adds the session to the user's list of sessions
        #     which the user is interested in attending to
        user = endpoints.get_current_user()
        if not user:
            raise endpoints.UnauthorizedException('Authorization required')

        # get a profile object
        prof = getProfileFromUser(user)

        wssk = request.websafeSessionKey
        session = ndb.Key(urlsafe=wssk).get()
        if not session:
            raise endpoints.NotFoundException(
                'No session found with key: %s' % wssk)

        if wssk in prof.sessionKeysInWhishlist:
                raise ConflictException(
                    "You have already added this session")

        # append this web safe session key to the list
        prof.sessionKeysInWhishlist.append(wssk)
        prof.put()
        retval = True
        return BooleanMessage(data=retval)

    @endpoints.method(message_types.VoidMessage, SessionForms,
                      path='wishlist',
                      http_method='GET', name='getSessionsInWishlist')
    def getSessionsInWishlist(self, request):
        # Get all the sessions that the user has added to their wishlist
        user = endpoints.get_current_user()
        if not user:
            raise endpoints.UnauthorizedException('Authorization required')
        prof = getProfileFromUser(user)

        # Get a list of session keys
        session_keys = [ndb.Key(urlsafe=wssk)
                        for wssk in prof.sessionKeysInWhishlist]
        sessions = ndb.get_multi(session_keys)

        # return set of SessionForm objects per Session
        return SessionForms(items=[self._copySessionToForm(session)
                                   for session in sessions]
                            )

    @endpoints.method(SessionQueryForms, SessionForms,
                      path='querySessions',
                      http_method='POST', name='querySessions')
    def querySessions(self, request):
        """Query for conferences."""
        sessions = self._getQuery(request)

        # return individual SessionForm object per Session
        # See also: _getQuery, _formatFilters, _lambdaFilter
        return SessionForms(
            items=[self._copySessionToForm(session)
                   for session in sessions]
        )

    @endpoints.method(message_types.VoidMessage, FeaturedSpeakerList,
                      path='get-featured-speaker',
                      http_method='GET', name='getFeaturedSpeaker')
    def getFeaturedSpeaker(self):
        # Get a json object of featured speakers
        #     and a list of their session
        # Featured Speaker: speakers who have more than one session
        #                   in a conference
        featured = memcache.get("featured_speakers")
        if not featured:
            return FeaturedSpeakerList(items=[])

        # We store jsonify string to mecache
        featured_json = json.loads(featured)

        # return list of FeaturedSpeaker
        # FeaturedSpeaker has two attr. speaker(name), sessionNames
        return FeaturedSpeakerList(
            items=[FeaturedSpeaker(
                speaker=speaker, sessionNames=featured_json[speaker])
                for speaker in featured_json]
        )
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    # - - - - Helper methods - - - - - - - - - - - - - - - - - -
    def _copySessionToForm(self, session):
        """Copy relevant fields from Conference to ConferenceForm."""
        sf = SessionForm()
        for field in sf.all_fields():
            if hasattr(session, field.name):
                if field.name == "websafeKey":
                    # URL safe session key
                    setattr(sf, field.name, session.key.urlsafe())
                elif field.name == "date":
                    # date type has to be stored as DateProperty
                    setattr(sf, field.name, str(getattr(session, field.name)))
                elif field.name == "startTime":
                    # startTime has to be stored as Integer,
                    #     so it is easy to Query,
                    #     such as Filter Sessions before 07 00 PM,
                    #     since 07 00 PM is converted to 1140
                    # See also _recoverIntToTime
                    setattr(sf, field.name,
                            self._recoverIntToTime(
                                getattr(session, field.name)
                            )
                            )
                elif field.name == "typeOfSession":
                    # type of session is of list type
                    tmp = []
                    for type in getattr(session, field.name):
                        tmp.append(getattr(TypeOfSession, str(type)))
                    setattr(sf, field.name, tmp)
                else:
                    setattr(sf, field.name, getattr(session, field.name))
        return sf

    def _createSessionObject(self, request):
        """Create Session object,
            returning SessionForm/request."""
        user = endpoints.get_current_user()
        if not user:
            raise endpoints.UnauthorizedException('Authorization required')
        user_id = getUserId(user)

        # Copy SessionForm/ProtoRPC Message into dict
        data = {field.name: getattr(request, field.name)
                for field in request.all_fields()}
        wsck = request.websafeConferenceKey
        conf = ndb.Key(urlsafe=wsck).get()

        if not conf:
            raise endpoints.NotFoundException('No such conference exist')

        if not conf.organizerUserId == user_id:
            raise endpoints.UnauthorizedException('Authorization required')

        # Delete properties which are not in the Session data model
        del data['websafeConferenceKey']
        del data['organizerDisplayName']

        if data['date']:
            data['date'] = datetime.strptime(data['date'], "%Y-%m-%d").date()

        # Convert dates from strings to Time objects
        #     and convert it to integer
        # See also: _convertTimeToInt
        if data['startTime']:
            start_time = self._convertTimeToInt(
                datetime.strptime(data['startTime'], "%I %M %p").time()
            )
            data['startTime'] = start_time

        # Allocate new Session ID with a given conference key as parent
        s_id = Session.allocate_ids(size=1, parent=conf.key)[0]
        # Make session key from ID
        s_key = ndb.Key(Session, s_id, parent=conf.key)
        data['key'] = s_key
        data['organizerUserId'] = request.organizerUserId = user_id
        data['conferenceKeyBelongTo'] = wsck

        # store a list of types of session to database
        type_of_session = []
        for type in data['typeOfSession']:
            type_of_session.append(str(getattr(TypeOfSession, str(type))))
        if len(type_of_session) > 0:
            data['typeOfSession'] = type_of_session

        Session(**data).put()

        if data["speaker"]:
            # If the inbound session form has speaker value
            #     call _cacheSession to determine
            #     if the speaker is a feature speaker,
            #     and if so, save the info. to memcache as a jsonified string
            # See also: _cacheSession
            self._cacheSession(data["speaker"], data['conferenceKeyBelongTo'])

        # return the result as an outbound session form message
        sf = SessionForm()
        for field in sf.all_fields():
            if hasattr(request, field.name):
                if field.name == "websafeKey":
                    # URL safe session key
                    setattr(sf, field.name, s_key.urlsafe())
                else:
                    setattr(sf, field.name, getattr(request, field.name))
        return sf

    @staticmethod
    def _cacheSession(speaker, confKey):
        # Check if the given speaker already exist,
        #     if so, append the speaker's name and the list of session
        #     to memcache with the key, ```featured_speakers```
        sessions = Session.query(ndb.AND(
            Session.speaker == speaker,
            Session.conferenceKeyBelongTo == confKey
        )).fetch(projection=[Session.name])

        if len(sessions) > 1:
            featured_speakers = memcache.get("featured_speakers")
            if not featured_speakers:
                memcache.set("featured_speakers", json.dumps(
                    [{speaker: [session.name for session in sessions]}]
                ))
            else:
                # If the memcache already exist,
                #     append a new info to the value already exists
                featured_speakers_dict = json.loads(featured_speakers)
                featured_speakers_dict[speaker] =\
                    [session.name for session in sessions]
                memcache.set("featured_speakers",
                             json.dumps(featured_speakers_dict))

    def _getQuery(self, request):
        """Return formatted query from the submitted filters."""
        q = Session.query()
        inequality_filters, filters = self._formatFilters(request.filters)

        if len(inequality_filters) <= 1:
            # if there is no inequality filter
            if len(inequality_filters) == 1:
                # If an inequality_filter exists,
                #     sort on the inequality filter first
                q = q.order(ndb.GenericProperty(
                    inequality_filters[0]["field"]
                )
                )
            q = q.order(Session.name)
            for filtr in filters:
                if filtr["field"] == "startTime":
                    # convert startTime to integer,
                    #     since it is stored as integer type
                    filtr["value"] = int(filtr["value"])
                formatted_query = ndb.query.FilterNode(
                    filtr["field"], filtr["operator"], filtr["value"])
                q = q.filter(formatted_query)
            return q
        else:
            # If there are more than two inequality filters,
            #     we need to handle inequality filters separately,
            #     and do in-memory filtering to get data we want
            inequality_filter_key_set = [x["field"]
                                         for x in inequality_filters]
            # Do equality filters first
            for filtr in filters:
                if filtr["field"] not in inequality_filter_key_set:
                    if filtr["field"] == "startTime":
                        filtr["value"] = int(filtr["value"])
                    formatted_query = ndb.query.FilterNode(
                        filtr["field"], filtr["operator"], filtr["value"])
                    q = q.filter(formatted_query)
            first_time = True
            for inequality_filter in inequality_filters:
                if first_time:
                    # Execute the first equality filter
                    if inequality_filter["field"] == "startTime":
                        inequality_filter["value"] =\
                            int(inequality_filter["value"])
                    formatted_query = ndb.query.FilterNode(
                        inequality_filter["field"],
                        inequality_filter["operator"],
                        inequality_filter["value"]
                    )
                    first_time = False
                    sessions = q.filter(formatted_query)
                else:
                    # From the second inequality filter
                    #     we need to preform list filtering
                    if inequality_filter["field"] == "startTime":
                        inequality_filter["value"] =\
                            int(inequality_filter["value"])
                    # Perform lambda function filtering for each session object
                    # lambda function returns true
                    #     if the session object satisfy the given filter
                    # See also: _lambaFilter
                    sessions = ifilter(
                        lambda x: self._lambaFilter(x, inequality_filter),
                        sessions
                    )
            return sessions

    def _lambaFilter(self, x, inequality_filter):
        if isinstance(getattr(x, inequality_filter["field"]), list):
            # If the filter value is of a type of list,
            #     such as type of session,
            #     change != to ```not in```
            return inequality_filter["value"]\
                   not in getattr(x, inequality_filter["field"])
        else:
            # By using OPERATOR LOOKUP Table we can get python operators
            # Example:
            #     - != : operator.ne
            #     - > : operator.gt
            return OPERATOR_LOOKUP[
                inequality_filter["operator"]
            ](getattr(x, inequality_filter["field"]),
              inequality_filter["value"]
              )

    def _formatFilters(self, filters):
        """Parse, check validity and format user supplied filters."""
        formatted_filters = []
        inequality_filters = []

        for f in filters:
            filtr = {field.name: getattr(f, field.name)
                     for field in f.all_fields()}

            try:
                filtr["field"] = SESSION_FIELDS[filtr["field"]]
                filtr["operator"] = OPERATORS[filtr["operator"]]
                if filtr["field"] == "startTime":
                    filtr['value'] = self._convertTimeToInt(
                        datetime.strptime(filtr['value'], "%I %M %p")
                    )
                if filtr["field"] == "date":
                    filtr['value'] =\
                        datetime.strptime(filtr['value'], "%Y-%m-%d").date()

            except KeyError:
                raise endpoints.BadRequestException(
                    "Filter contains invalid field or operator.")

            # Every operation except "=" is an inequality
            if filtr["operator"] != "=":
                # check if inequality operation
                #     has been used in previous filters
                # disallow the filter if inequality was performed
                #     on a different field before
                # track the field
                #     on which the inequality operation is performed
                # store inequality filters separately
                inequality_filters.append(filtr)

            formatted_filters.append(filtr)
        return (inequality_filters, formatted_filters)

    def _convertTimeToInt(self, timeData):
        """
        convert a time property to an integer
        Usage: SessionForm -> Session database model
        :param timeData: strptime(hour, minute, AM/PM).time()
        :return: integer
        """
        try:
            return timeData.hour * 60 + timeData.minute
        except:
            raise endpoints.BadRequestException("Invalid time format")

    def _recoverIntToTime(self, timeInteger):
        """
        recover a time property from an integer
        Usage: Session database model -> SessionForm
        :param timeInteger
        :return: strptime(hour, minute, AM/PM).time()
        """
        hour = int(timeInteger / 60)
        loc = "AM"
        if hour > 12:
            hour = hour - 12
            loc = "PM"
        minute = timeInteger % 60
        return " ".join([str(hour), str(minute), loc])
