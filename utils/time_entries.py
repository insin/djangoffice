from datetime import timedelta

class DayTimeEntry:
    """
    Time booked for a task by a user on a particular day.
    """
    def __init__(self, user, task, date, hours, is_overtime=False):
        self.user = user
        self.task = task
        self.date = date
        self.hours = hours
        self.is_overtime = is_overtime

    def __str__(self):
        return '%s hours on %s' % (self.hours, self.date)

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
        timesheet = time_entry.timesheet
        day_count = 0
        for i, day_attr in enumerate(DAY_ATTRS):
            if getattr(time_entry, day_attr) > 0:
                day_entry = DayTimeEntry(timesheet.user, time_entry.task,
                    timesheet.week_commencing + timedelta(days=i),
                    getattr(time_entry, day_attr))
                if day_attr == 'overtime':
                    day_entry.date = timesheet.week_commencing
                    day_entry.is_overtime = True
                daily_entries.append(day_entry)
    return daily_entries
