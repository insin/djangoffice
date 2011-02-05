import unittest
from datetime import date

from django.http import Http404

from djangoffice.utils.dates import (is_week_commencing_date,
    is_week_ending_date, week_commencing_date, week_ending_date)
from djangoffice.views.timesheets import week_commencing_date_or_404

class DateUtilTest(unittest.TestCase):
    def testIsWeekCommencingDate(self):
        self.assertTrue(is_week_commencing_date(date(2007, 7, 23)))
        self.assertFalse(is_week_commencing_date(date(2007, 7, 24)))
        self.assertFalse(is_week_commencing_date(date(2007, 7, 25)))
        self.assertFalse(is_week_commencing_date(date(2007, 7, 26)))
        self.assertFalse(is_week_commencing_date(date(2007, 7, 27)))
        self.assertFalse(is_week_commencing_date(date(2007, 7, 28)))
        self.assertFalse(is_week_commencing_date(date(2007, 7, 29)))

    def testIsWeekEndingDate(self):
        self.assertFalse(is_week_ending_date(date(2007, 7, 23)))
        self.assertFalse(is_week_ending_date(date(2007, 7, 24)))
        self.assertFalse(is_week_ending_date(date(2007, 7, 25)))
        self.assertFalse(is_week_ending_date(date(2007, 7, 26)))
        self.assertFalse(is_week_ending_date(date(2007, 7, 27)))
        self.assertFalse(is_week_ending_date(date(2007, 7, 28)))
        self.assertTrue(is_week_ending_date(date(2007, 7, 29)))

    def testWeekCommencingDateOr404(self):
        # Week commencing date
        self.assertEquals(date(2007, 7 , 23), week_commencing_date_or_404('2007', '07', '23'))

        # Non week commencing dates
        self.assertRaises(Http404, week_commencing_date_or_404, '2007', '07', '24')
        self.assertRaises(Http404, week_commencing_date_or_404, '2007', '07', '25')
        self.assertRaises(Http404, week_commencing_date_or_404, '2007', '07', '26')
        self.assertRaises(Http404, week_commencing_date_or_404, '2007', '07', '27')
        self.assertRaises(Http404, week_commencing_date_or_404, '2007', '07', '28')
        self.assertRaises(Http404, week_commencing_date_or_404, '2007', '07', '29')

        # Invalid date parts
        self.assertRaises(Http404, week_commencing_date_or_404, '2007', '29', '600')
        self.assertRaises(Http404, week_commencing_date_or_404, 'a', 'b', 'c')

    def testWeekCommencingDate(self):
        week_commencing = date(2007, 7, 23)
        self.assertEquals(week_commencing, week_commencing_date(date(2007, 7, 23)))
        self.assertEquals(week_commencing, week_commencing_date(date(2007, 7, 24)))
        self.assertEquals(week_commencing, week_commencing_date(date(2007, 7, 25)))
        self.assertEquals(week_commencing, week_commencing_date(date(2007, 7, 26)))
        self.assertEquals(week_commencing, week_commencing_date(date(2007, 7, 27)))
        self.assertEquals(week_commencing, week_commencing_date(date(2007, 7, 28)))
        self.assertEquals(week_commencing, week_commencing_date(date(2007, 7, 29)))

    def testWeekEndingDate(self):
        week_ending = date(2007, 7, 29)
        self.assertEquals(week_ending, week_ending_date(date(2007, 7, 23)))
        self.assertEquals(week_ending, week_ending_date(date(2007, 7, 24)))
        self.assertEquals(week_ending, week_ending_date(date(2007, 7, 25)))
        self.assertEquals(week_ending, week_ending_date(date(2007, 7, 26)))
        self.assertEquals(week_ending, week_ending_date(date(2007, 7, 27)))
        self.assertEquals(week_ending, week_ending_date(date(2007, 7, 28)))
        self.assertEquals(week_ending, week_ending_date(date(2007, 7, 29)))
