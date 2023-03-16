from googfit import GoogFit
from datetime import datetime

# Daily Step Count
token = 'YOUR_ACCESS_TOKEN'
gf = GoogFit(token, timezone='US/Pacific')
print(gf.daily_steps(datetime.today()))