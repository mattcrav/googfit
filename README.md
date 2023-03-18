# googfit - Python 3 Wrapper for Google Fitness API
googfit is a Python 3 wrapper for the Google Fitness API focused on working with <a href="https://www.concept2.com/">Concept2</a> rowing data synced with Google Fit.  Following methods have been implemented.

- daily_steps() - takes a datetime object and returns total steps for that day
- daily_concept2() - takes a datetime object and returns a list of Concept2 rowing maching workouts on that day.  Workout object includes duration, distance, average watts and watt-hours.

to use, instantiate GoogFit class with appropriate refresh_token (see Setup) and timezone.  To get your timezone, find appropriate TZ database name on https://en.wikipedia.org/wiki/List_of_tz_database_time_zones.  Assumes GMT if no timzone provided.

```python
from googfit import GoogFit
from datetime import datetime

gf = GoogFit(timezone='US/Pacific')
day = datetime.today()
print(f'Total Steps: {gf.daily_steps(day)}')
```

## Setup
You can access the api methods through the GoogFit class which requires a refresh_token for an authenticated user of the client being used.  Authentication isn't integrated in the code but I've added a couple static helper methods in the GoogFit class. See https://developers.google.com/identity/protocols/oauth2/native-app for details on the authentication process.

- auth_url() - this will generate the authentication url which you can use in a browser to get your auth_token
- exchange_auth() - passing your auth_token to this method will return your refresh_token in json format

client data is read from <u>client_secret.json</u> which has the following format.  You can download a file in this format from Google Cloud Console https://console.cloud.google.com/ if you create your client there.

client_id, token_uri, client_secret, and redirect_uris are required.
```json
{
    "installed":{
        "client_id":"",
        "project_id":"",
        "auth_uri":"",
        "token_uri":"",
        "auth_provider_x509_cert_url":"",
        "client_secret":"",
        "redirect_uris":[""]
    }
    
}
```
Once you have your refresh_token, you can pass it to the GoogleFit class on instantiation or store it in <u>refresh_token.json</u>
```json
{
    "refresh_token":{""}
}
```
