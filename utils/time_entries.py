"""
Utilities for working with TimeEntry objects.
"""
from datetime import timedelta

class DayTimeEntry:
    """
    Time booked for a task by a user on a particular day.
    """
    def __init__(self, user_id, task_id, date, hours, overtime=False):
        self.user_id, self.task_id = user_id, task_id
        self.date = date
        self.hours = hours
        self.overtime = overtime

DAY_ATTRS = ('mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun', 'overtime')
def weekly_to_daily_entries(time_entries):
    """
    Converts a list of ``TimeEntry`` instances to ``DayTimeEntry``
    instances, one for each day on which time is booked in each
    ``TimeEntry``.

    Any overtime booked will be marked as occurring on the first day
    of the week.
    """
    daily_entries = []
    for time_entry in time_entries:
        day_count = 0
        for i, day_attr in enumerate(DAY_ATTRS):
            if getattr(time_entry, day_attr) > 0:
                day_entry = DayTimeEntry(time_entry.user_id, time_entry.task_id,
                    time_entry.week_commencing + timedelta(days=i),
                    getattr(time_entry, day_attr))
                if day_attr == 'overtime':
                    day_entry.date = time_entry.week_commencing
                    day_entry.overtime = True
                daily_entries.append(day_entry)
    return daily_entries
