import endpoints
from conference import ConferenceApi
from user import UserApi
from session import SessionApi


# registers API
# Registers api endpoints in the modules below:
#     - UserApi: user.py
#     - ConferenceApi: conference.py
#     - SessionApi: session.py
api = endpoints.api_server([UserApi, ConferenceApi, SessionApi])
