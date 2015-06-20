import json
import os
import time
import uuid

from google.appengine.api import urlfetch
from google.appengine.ext import ndb

from models.profile import Profile, TeeShirtSize


def getUserId(user, id_type="email"):
    """
    Retrieve User id from a given user object
    :param user: A current user object from API endpoint.
        Example: user = endpoints.get_current_user()
    :param id_type: define return type of this function.
        - email: return user email address
        - oauth: return user information from google+ oauth.
        - custom: return current user id or generate unique id
    :return: email, oauth user id, or user id of the corresponding entity
    """
    if id_type == "email":
        return user.email()

    if id_type == "oauth":
        """A workaround implementation for getting userid."""
        auth = os.getenv('HTTP_AUTHORIZATION')
        bearer, token = auth.split()
        token_type = 'id_token'
        if 'OAUTH_USER_ID' in os.environ:
            token_type = 'access_token'
        url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?%s=%s'
               % (token_type, token))
        user = {}
        wait = 1
        for i in range(3):
            resp = urlfetch.fetch(url)
            if resp.status_code == 200:
                user = json.loads(resp.content)
                break
            elif resp.status_code == 400 and 'invalid_token' in resp.content:
                url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?%s=%s'
                       % ('access_token', token))
            else:
                time.sleep(wait)
                wait = wait + i
        return user.get('user_id', '')

    if id_type == "custom":
        # implement your own user_id creation and getting algorythm
        # this is just a sample that queries datastore for an existing profile
        # and generates an id if profile does not exist for an email
        profile = Profile.query(Profile.mainEmail == user.email())
        if profile:
            return profile.id()
        else:
            return str(uuid.uuid1().get_hex())


def getProfileFromUser(user):
    """
    Return user Profile from datastore, creating new one if non-existent.
    :param user: A current user object from API endpoint.
        Example: user = endpoints.get_current_user()
    :return: Profile object
    """
    user_id = getUserId(user)
    p_key = ndb.Key(Profile, user_id)
    profile = p_key.get()

    if not profile:
        profile = Profile(
            key=p_key,
            displayName=user.nickname(),
            mainEmail=user.email(),
            teeShirtSize=str(TeeShirtSize.NOT_SPECIFIED),
        )
        profile.put()

    # return Profile
    return profile
