import json
import requests
from io import StringIO
from datetime import datetime, timedelta
import calendar
import pytz


class GoogFit:
    def __init__(self, token: str, timezone: str=None) -> None:
        self.token = token
        self.timezone = timezone
        self.base_url = 'https://www.googleapis.com/fitness/v1/users/me/dataSources/'

    def daily_steps(self, day: datetime) -> int:
        """
        Daily total estimated steps
        requires https://www.googleapis.com/auth/fitness.activity.read authorization.
        """
        d = datetime(day.year, day.month, day.day)
        if self.timezone is not None:
            d = pytz.timezone(self.timezone).localize(d)
        start = calendar.timegm(d.utctimetuple()) * 10**9
        end = calendar.timegm((d + timedelta(hours=24)).utctimetuple()) * 10**9
        url = self.base_url + f'derived:com.google.step_count.delta:com.google.android.gms:estimated_steps/datasets/{start}-{end}'

        ses = requests.session()
        ses.headers.update({'Authorization': f'Bearer {self.token}'})
        r = ses.get(url)
        j = json.load(StringIO(r.text))
        if r.status_code == 401:
            raise ConnectionError(j['error']['message'])
        
        return sum([p['value'][0]['intVal'] for p in j['point']])