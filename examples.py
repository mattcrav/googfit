from googfit import GoogFit
from datetime import datetime, timedelta

# Initialize wrapper class with timezone, refresh_token from refresh_token.json
gf = GoogFit(timezone='US/Pacific')
day = datetime.today()

# Convert datetime to epoch nanoseconds
print(f"---{day.strftime('%m-%d-%Y')}---")
print(f'Start of Day (nanos): {gf.get_nano(day)}')
print(f'End of Day (nanos): {gf.get_nano(day + timedelta(hours=24))}')
print()

# Daily Step Count
print(f'Total Steps: {gf.daily_steps(day)}')
print()

# Concept2 Workouts
workouts = gf.daily_concept2(day)
print(f'Concept2 Workouts ({len(workouts)} Sessions)')
print()
i = 1
for w in workouts:
    print(f'-Workout #{i}-')
    print(f'Start (nanos): {w.start}')
    print(f'End (nanos): {w.end}')
    print(f'Duration (seconds): {w.duration}')
    print(f'Distance (meters): {w.distance}')
    print(f'Average Watts: {w.watts}')
    print(f'Watt-Hours: {w.watthours}')
    print()
    i += 1