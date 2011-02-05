"""
Invoice time calculations.
"""
import operator
from decimal import Decimal

from django.db.models.query import Q

from djangoffice.models import TimeEntry
from djangoffice.utils.time_entries import weekly_to_daily_entries

class RateNotFound(Exception):
    """A billing rate could not be found for time which was booked."""
    pass

class HoursAndCost:
    def __init__(self):
        self.hours = Decimal(0)
        self.cost = Decimal(0)

    def add(self, hours, cost):
        self.hours += hours
        self.cost += cost

class InvoiceTimeCalculation:
    def __init__(self, job, start_period=None, end_period=None, include_invoiced=False):
        self.job = job
        self.start_period, self.end_period = start_period, end_period
        self.include_invoiced = include_invoiced
        self.exchange_rate = None

        # Calculated attributes
        self.total_hours = 0.0
        self.total_cost = 0.0
        self.by_task = {}
        self.by_user_and_task = {}
        self.by_date_and_user = {}

    def calculate(self, rate_lookup, invoice_driven_by):
        """
        Determines which TimeEntries will be included in the invoice,
        calculates the cost of hours booked using the given rate lookup
        and totals the hours and costs in various ways.
        """
        # Retrieve TimeEntries to be included in the invoice
        filters = [Q(task__job=job), Q(approved=True)]
        if self.start_period is not None:
            filters.append(Q(week_commencing__gte=self.start_date))
        if self.end_period is not None:
            filters.append(Q(week_commencing__lte=self.start_date))
        if not self.include_invoiced:
            filters.append(Q(invoice__isnull=False))
        time_entries = list(TimeEntry.objects.filter(map(operator._and, filters)))
        self.time_entry_ids = [te.id for te in time_entries]

        # Convert time entries to a daily format
        day_time_entries = weekly_to_daily_entries(time_entries)

        rate_by_pk_attr = {
            u'U': 'user_id',
            u'T': 'task_id',
        }[invoice_driven_by]

        for entry in day_time_entries:
            # Calculate the cost of the time entry
            rate = rate_lookup.get_applicable_rate(
                getattr(entry, rate_by_pk_attr), entry.date)
            if rate is None:
                raise RateNotFound(u'An applicable billing rate could not be found.')
            rate_amount = entry.overtime and rate.overtime_rate or rate.standard_rate
            cost = entry.hours * rate_amount
            if self.exchange_rate is not None:
                cost = cost * self.exchange_rate

            # Update calculated attributes with the hours and cost for the
            # time entry.
            self.total_hours += entry.hours
            self.total_cost += cost
            self.by_task.setdefault(entry.task_id,
                                    HoursAndCost()).add(entry.hours, cost)
            self.by_user_and_task.setdefault(entry.user_id, {}) \
                .setdefault(entry.task_id, HoursAndCost()).add(entry.hours, cost)
            self.by_date_and_user.setdefault(entry.date, {}) \
                .setdefault(entry.user_id, HoursAndCost()).add(entry.hours, cost)
