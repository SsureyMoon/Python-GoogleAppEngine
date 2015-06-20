import endpoints
from protorpc import message_types
from protorpc import remote

import utils
from core import EMAIL_SCOPE, API_EXPLORER_CLIENT_ID
from settings import WEB_CLIENT_ID
from models.profile import ProfileForm, TeeShirtSize, ProfileMiniForm


@endpoints.api(name='user',
               version='v1',
               allowed_client_ids=[WEB_CLIENT_ID, API_EXPLORER_CLIENT_ID],
               scopes=[EMAIL_SCOPE])
class UserApi(remote.Service):
    """User API v0.1
    This class is of use/profile api. This class is consist of
    endpoint methods and helper methods.

    Attributes:
        @endpoints
            - getProfile(websafeConferenceKey): retrieve profile of
                a current use
                See also: _doProfile
            - saveProfile(): Store a current user's profile
                with ```ProfileMiniForm``` which is an inbound form message
                See also: _doProfile, models.profile.ProfileMiniForm

        helper:
            _copyProfileToForm:
                convert data from database into Conference form message
            _doProfile: convert data from inbound from message,
                so it fits in profile model.
                Create/Update  a profile entity
    """

    # - - - - API endpoints - - - - - - - - - - - - - - - - - - - - - - - - - -
    @endpoints.method(message_types.VoidMessage, ProfileForm,
                      path='profile', http_method='GET', name='getProfile')
    def getProfile(self, request):
        """Return user profile."""
        return self._doProfile()

    @endpoints.method(ProfileMiniForm, ProfileForm,
                      path='profile', http_method='POST', name='saveProfile')
    def saveProfile(self, request):
        """Update & return user profile."""
        return self._doProfile(request)
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    # - - - Helper methods - - - - - - - - - - - - - - - - - - - -
    def _copyProfileToForm(self, prof):
        """Copy relevant fields from Profile to ProfileForm."""
        pf = ProfileForm()
        for field in pf.all_fields():
            if hasattr(prof, field.name):
                # convert t-shirt string to Enum; just copy others
                if field.name == 'teeShirtSize':
                    setattr(pf, field.name,
                            getattr(TeeShirtSize, getattr(prof, field.name)))
                else:
                    setattr(pf, field.name, getattr(prof, field.name))
        pf.check_initialized()
        return pf

    def _doProfile(self, save_request=None):
        """Get user Profile and return to user, possibly updating it first."""
        # get user Profile
        user = endpoints.get_current_user()
        prof = utils.getProfileFromUser(user)

        # if saveProfile(), process user-modifyable fields
        if save_request:
            for field in ('displayName', 'teeShirtSize'):
                if hasattr(save_request, field):
                    val = getattr(save_request, field)
                    if val:
                        setattr(prof, field, str(val))
                prof.put()

        # return ProfileForm
        return self._copyProfileToForm(prof)
