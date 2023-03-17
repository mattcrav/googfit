import json
import requests
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
        concept2 pace to watt formula 
        https://www.concept2.com/indoor-rowers/training/calculators/watts-calculator
        """
        return 2.8 / (self.duration / self.distance)**3
    
    @property
    def watthours(self):
        return self.watts * (self.duration / 60**2)


class GoogFit:
    def __init__(self, token: str, timezone: str=None) -> None:
        self.token = token
        self.timezone = timezone
        self.base_url = 'https://www.googleapis.com/fitness/v1/users/me/dataSources/'

    def get_nano(self, dt: datetime) -> int:
        """
        Convert datetime into epoch nanosecond time
        """
        if self.timezone is not None:
            d = pytz.timezone(self.timezone).localize(dt)
        return calendar.timegm(d.utctimetuple()) * 10**9
    
    def daily_steps(self, day: datetime) -> int:
        """
        Daily total estimated steps

        requires https://www.googleapis.com/auth/fitness.activity.read authorization.
        """
        d = datetime(day.year, day.month, day.day)
        start = self.get_nano(d)
        end = self.get_nano(d + timedelta(hours=24))
        url = self.base_url + f'derived:com.google.step_count.delta:com.google.android.gms:estimated_steps/datasets/{start}-{end}'

        ses = requests.session()
        ses.headers.update({'Authorization': f'Bearer {self.token}'})
        r = ses.get(url)
        j = json.load(StringIO(r.text))
        if r.status_code == 401:
            raise ConnectionError(j['error']['message'])
        
        return sum([p['value'][0]['intVal'] for p in j['point']])
    
    def daily_concept2(self, day: datetime) -> List[Workout]:
        """
        Get list of concept2 rowing machine workouts for the day
        returns a list of Workout objects
        Use distance and duration to calculate work done since the calories value stored in Fit doesn't include rest time

        requires https://www.googleapis.com/auth/fitness.activity.read authorization.
        requires https://www.googleapis.com/auth/fitness.location.read authorization
        """
        d = datetime(day.year, day.month, day.day)
        start = self.get_nano(d)
        end = self.get_nano(d + timedelta(hours=24))
        seg_url = self.base_url + f'raw:com.google.activity.segment:com.concept2.ergdata:/datasets/{start}-{end}'
        dist_url = self.base_url + f'raw:com.google.distance.delta:com.concept2.ergdata:/datasets/{start}-{end}'

        # get workouts
        ses = requests.session()
        ses.headers.update({'Authorization': f'Bearer {self.token}'})
        r = ses.get(seg_url)
        j = json.load(StringIO(r.text))
        if r.status_code == 401:
            raise ConnectionError(j['error']['message'])
        
        workouts = []
        for p in j['point']:
            w = Workout(int(p['startTimeNanos']), int(p['endTimeNanos']))
            workouts.append(w)

        # sum distance per workout
        ses = requests.session()
        ses.headers.update({'Authorization': f'Bearer {self.token}'})
        r = ses.get(dist_url)
        j = json.load(StringIO(r.text))
        if r.status_code == 401:
            raise ConnectionError(j['error']['message'])
        
        currwork = None
        for p in j['point']:
            for w in workouts:
                if int(p['startTimeNanos']) == w.start:
                    currwork = w
            currwork.distance += int(p['value'][0]['fpVal'])

        return workouts