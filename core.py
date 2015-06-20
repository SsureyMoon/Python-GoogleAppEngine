import endpoints
import operator


# Default conference info.
DEFAULTS = {
    "city": "Default City",
    "maxAttendees": 0,
    "seatsAvailable": 0,
    "topics": ["Default", "Topic"],
}

# Convert operators from front-end/api form to SQL operators
OPERATORS = {
    'EQ': '=',
    'GT': '>',
    'GTEQ': '>=',
    'LT': '<',
    'LTEQ': '<=',
    'NE': '!='
}

# Convert field names from front-end/api to fields in Data model
CONF_FIELDS = {
    'CITY': 'city',
    'TOPIC': 'topics',
    'MONTH': 'month',
    'MAX_ATTENDEES': 'maxAttendees',
}

# Convert field names from front-end/api to fields in Data model
SESSION_FIELDS = {
    'NAME': 'name',
    'SPEAKER': 'speaker',
    'HIGHLIGHTS': 'highlights',
    'TYPE_OF_SESSION': 'typeOfSession',
    'START_TIME': 'startTime',
    'DATE': 'date',
}

# Operator lookup tables for multi inequality filters
# Convert SQL operators to Python operators available for in-memory filtering
OPERATOR_LOOKUP = {
    '>': operator.gt,
    '>=': operator.ge,
    '<': operator.lt,
    '<=': operator.le,
    '!=': operator.ne,
    '=': operator.eq
}

EMAIL_SCOPE = endpoints.EMAIL_SCOPE
API_EXPLORER_CLIENT_ID = endpoints.API_EXPLORER_CLIENT_ID
