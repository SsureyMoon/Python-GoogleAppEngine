# Python-Google App Engine-API
Simple project in Python and [Google app engine][1]

## How it works

1. HTTP requests and responses are handled by Google App engine endpoints.
2. User profiles, conferences, and Session are stored in [ndb][2]
3. Google + OAuth is needed to create a conference and a session
4. Handle multiple inequality filters by in-memory filtering
5. API can be tested by [Google api explorer][3]

## Dependencies
- [Python][4] version 2.7.x or higher

## Getting Started

### Cloning the source code.
```bash
git clone https://github.com/SsureyMoon/Simple-Python-GoogleAppEngine.git
```

### Setup environment
Update the value of `application` in `app.yaml` to the app ID you have registered in the App Engine admin console and would like to use to host your instance of this sample. Visit [google developer console][5]

In app.yaml:
```yaml
application: <your app id>
version: 1
runtime: python27
api_version: 1
threadsafe: yes
```

Update the values at the top of `settings.py` to reflect the respective client IDs you have registered in the [Developer Console][4].
In settings.py:
```python
WEB_CLIENT_ID = '<your client id from google developer console>'

```

Update the value of CLIENT_ID in `static/js/app.js` to the Web client ID
In static/js/app.js:
```javascript
app.factory('oauth2Provider', function ($modal) {
    var oauth2Provider = {
        CLIENT_ID: '<your client id from google developer console>',
        SCOPES: 'email profile',
        signedIn: false
    }
```

** Please do not commit your code with your web client id. You can avoid that by running this command: **
```bash
git update-index --assume-unchanged app.yaml settings.py static/js/app.js
```

### Run and test the server
- Download, Install and Open [GoogleAppEngineLauncher][6]
- File -> New Application -> add path of this project
- Click `Run` button
- Test your application by visiting http://localhost:8000
- Test your api enpoints by visiting http://localhost:8000/_ah/api/explorer

### Deploy your application
- Click Deploy button
- Test your application by visiting http://*your app id*.appspot.com
- Test your api enpoints by visiting http://*your app id*.appspot.com/_ah/api/explorer

## API endpoints

### User Api
  * GET /profile:  Return the current logged in user's profile
  * POST /profile: Save & return user profile.
      * Form Data: 
        * displayName: String
        * teeShirtSize: one of [NOT_SPECIFIED, XS_M, XS_W, S_M, S_W, M_M, M_W, L_M, L_W, XL_M, XL_W, XXL_M, XXL_W, XXXL_M, XXXL_W]

---

### Conference Api
  * GET /conference/{websafeConferenceKey}: Return conference info. by websafeConferenceKey
  * POST /conference: Create a new conference entity
      * Form Data:
        * name: String, *required
        * description: String
        * organizerUserId: String
        * topics: List of String
        * city: String
        * startDate: Date Format
        * month: Integer
        * maxAttendees: Integer
        * seatsAvailable: Integer
        * endDate: Date Format
        * organizerUserId: String
        * organizerDisplayName: String
  * PUT /conference/{websafeConferenceKey}: "Update conference w/provided fields & return w/updated info.
      * Form Data: same as `POST /conference`
  * POST /queryConferences: Query for conferences
      * Form Data: List of Query forms
        * Query form:
            * Field: String
            * Operator: one of [EQ, GT, GTEQ, LT, LTEQ, NE]
            * Value: String
  * GET /getConferencesCreated: Get a list of conference which the current user has created
  * GET /getConferencesToAttend: Get list of conferences that user has registered for
  * POST /conference/{websafeConferenceKey}: Register user for selected conference.
      * Form data: 
        * websafeConferenceKey: String
  * DELETE /conference/{websafeConferenceKey}: Unregister user for selected conference.
      * Form data: 
        * websafeConferenceKey: String
  * GET /conference/announcement/get: return an existing announcement from Memcache or an empty string

***

### Session Api
  * GET /conference/{websafeConferenceKey}/session: Given a conference, return all sessions
  * GET /conference/{websafeConferenceKey}/session/{typeOfSession}: Given a conference, return all session of a specified type (eg lecture, keynote, workshop)
      * Arguements:
        * typeOfSession: one of [NOT_SPECIFIED, LECTURE, KEYNOTE, WORKSHOP, DEMO, SOCIAL]
  * GET /session/{speaker}: Given a speaker, return all sessions given by this particular speaker, across all conferences
      * Arguements:
        * speaker: String
  * POST /conference/{websafeConferenceKey}/session: Create a session object from form data and save it to database, return a session object created
      * Arguements:
        * websafeConferenceKey: String, *required
      * Form Data:
        * organizerUserId: messages.StringField(1)
        * name: String, *required
        * highlights: String
        * speaker: String
        * duration: String, Eg. 1h, 30m, 2h30m
        * typeOfSession: List of String. Sub list of [NOT_SPECIFIED, LECTURE, KEYNOTE, WORKSHOP, DEMO, SOCIAL]
        * date: Date string
        * startTime: Time String, Eg. 07 00 PM, 11:00 AM, etc..
        * organizerDisplayName: String
  * POST /wishlist/session/{websafeSessionKey}: Adds the session to the user's list of sessions which the user is interested in attending to
      * Arguements:
        * websafeSessionKey: String, *required
  * GET /wishlist: Get all the sessions that the user has added to their wishlist
  * POST /querySessions: Query for conferences
      * Form Data: List of Query forms
        * Query form:
            * Field: String
            * Operator: one of [EQ, GT, GTEQ, LT, LTEQ, NE]
            * Value: String
  * GET /get-featured-speaker: get a list of featured speakers


[1]: https://developers.google.com/appengine
[2]: https://cloud.google.com/appengine/docs/python/ndb/
[3]: https://developers.google.com/apis-explorer/#p/
[4]: http://python.org
[5]: https://console.developers.google.com/project
[6]: https://cloud.google.com/appengine/downloads
