import json
import requests
import urllib.parse
from io import StringIO
from datetime import datetime, timedelta
import calendar
import pytz
from typing import List

class Workout:
    def __init__(self, start, end):
        self.start = start
        self.end = end
        self.type = 'Rowing Machine'
        self.distance = 0

    @property
    def duration(self):
        """
        total duration of workout in seconds
        """
        return (self.end - self.start) / 10**9
    
    @property
    def watts(self):
        """
        calculated using concept2 pace to watt formula 

        https://www.concept2.com/indoor-rowers/training/calculators/watts-calculator

        use distance and duration to calculate work done since the calories value stored in Fit doesn't include rest time
        """
        return 2.8 / (self.duration / self.distance)**3
    
    @property
    def watthours(self):
        return self.watts * (self.duration / 60**2)


class GoogFit:
    def __init__(self, refresh_token: str=None, timezone: str=None) -> None:
        if refresh_token is None:
            with open('refresh_token.json', 'r') as f:
                j = json.load(f)
                refresh_token = j['refresh_token']
        self.refresh_token = refresh_token
        self.refresh_count = 0
        self.token = self.refresh(self.refresh_token)
        self.timezone = timezone
        self.base_url = 'https://www.googleapis.com/fitness/v1/users/me/dataSources/'

    @staticmethod
    def auth_url():
        """
        This helper method generates the necessary url to authenticate against your client

        uses client details in client_secret.json

        returns auth_token in local host
        """
        with open('client_secret.json', 'r') as f:
            j = json.load(f)
        payload = {
            'redirect_uri': j['installed']['redirect_uris'][0],
            'response_type': 'code',
            'client_id': j['installed']['client_id'],
            'scope': 'https%3A%2F%2Fwww.googleapis.com%2Fauth%2Ffitness.activity.read+https%3A%2F%2Fwww.googleapis.com%2Fauth%2Ffitness.location.read',
            'access_type': 'offline'
        }  

        return 'https://accounts.google.com/o/oauth2/v2/auth?' + urllib.parse.urlencode(payload)

    @staticmethod  
    def exchange_auth(auth_token):
        """
        This helper method can be used to exchange your auth_token for a refresh_token

        returns the server token response which includes refresh_token

        refresh_token should go in refresh_token.json if you want to auto-load
        """
        with open('client_secret.json', 'r') as f:
            j = json.load(f)
        payload = {
            'code': auth_token,
            'redirect_uri': j['installed']['redirect_uris'][0],
            'client_id': j['installed']['client_id'],
            'client_secret': j['installed']['client_secret'],
            'grant_type': 'authorization_code'
        }  
        ses = requests.session()
        r = ses.post(j['installed']['token_uri'], data=payload)

        return r.text

    def refresh(self, refresh_token):
        """
        exchanges your refresh_token for a new access_token for API calls

        automatically refreshes when instantiating class

        when api methods detects old access_token, refreshes
        """
        self.refresh_count += 1
        print(f'refreshing access token (refresh #{self.refresh_count})...')
        with open('client_secret.json', 'r') as f:
            j = json.load(f)
        payload = {
            'refresh_token': refresh_token,
            'client_id': j['installed']['client_id'],
            'client_secret': j['installed']['client_secret'],
            'grant_type': 'refresh_token'
        }  
        ses = requests.session()
        r = ses.post(j['installed']['token_uri'], data=payload)
        j = json.load(StringIO(r.text))
        print(f"new token expires in {j['expires_in']} seconds")

        return j['access_token']

    def get_nano(self, dt: datetime) -> int:
        """
        Convert datetime into epoch nanosecond time

        most API calls reguire start and end time in epoch nanoseconds
        """
        if self.timezone is not None:
            d = pytz.timezone(self.timezone).localize(dt)
        return calendar.timegm(d.utctimetuple()) * 10**9
    
    def get_json_response(self, session, url):
        """
        Make API call and get json response

        If access token has expired, refresh and try again
        """
        session.headers.update({'Authorization': f'Bearer {self.token}'})
        r = session.get(url)
        if r.status_code == 401:
            self.token = self.refresh(self.refresh_token)
            session.headers.update({'Authorization': f'Bearer {self.token}'})
            r = session.get(url)
        return json.load(StringIO(r.text))

    def daily_steps(self, day: datetime) -> int:
        """
        Daily total estimated steps

        Best match for Android App display

        requires https://www.googleapis.com/auth/fitness.activity.read authorization
        """
        d = datetime(day.year, day.month, day.day)
        start = self.get_nano(d)
        end = self.get_nano(d + timedelta(hours=24))
        url = self.base_url + f'derived:com.google.step_count.delta:com.google.android.gms:estimated_steps/datasets/{start}-{end}'

        ses = requests.session()

        j = self.get_json_response(ses, url)
        
        return sum([p['value'][0]['intVal'] for p in j['point']])
    
    def daily_concept2(self, day: datetime) -> List[Workout]:
        """
        Get list of concept2 rowing machine workouts for the day

        returns a list of Workout objects

        requires https://www.googleapis.com/auth/fitness.activity.read authorization

        requires https://www.googleapis.com/auth/fitness.location.read authorization
        """
        d = datetime(day.year, day.month, day.day)
        start = self.get_nano(d)
        end = self.get_nano(d + timedelta(hours=24))
        seg_url = self.base_url + f'raw:com.google.activity.segment:com.concept2.ergdata:/datasets/{start}-{end}'
        dist_url = self.base_url + f'raw:com.google.distance.delta:com.concept2.ergdata:/datasets/{start}-{end}'

        ses = requests.session()

        # get workouts
        j = self.get_json_response(ses, seg_url)
        
        workouts = []
        for p in j['point']:
            w = Workout(int(p['startTimeNanos']), int(p['endTimeNanos']))
            workouts.append(w)

        # sum distance per workout
        j = self.get_json_response(ses, dist_url)

        currwork = None
        for p in j['point']:
            for w in workouts:
                if int(p['startTimeNanos']) == w.start:
                    currwork = w
            currwork.distance += int(p['value'][0]['fpVal'])

        return workouts