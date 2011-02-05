import datetime

from django.test import TestCase

from djangoffice.models import Invoice

class InvoiceManagerTest(TestCase):
    """
    Tests for custom manager methods.
    """
    fixtures = ['initial_test_data']

    def testWithJobDetails(self):
        Invoice.objects.create(job_id=1, number=1, type='W',
            date=datetime.date.today(), amount_invoiced=123)
        invoice = Invoice.objects.with_job_details().get(pk=1)
        self.assertEquals(0, invoice.job_number)
        self.assertEquals(u'Admin Job', invoice.job_name)
        self.assertEquals(u'GBP', invoice.job_fee_currency)
        self.assertEquals(u'Generitech', invoice.client_name)
        self.assertEquals(u'OfficeAid', invoice.primary_contact_first_name)
        self.assertEquals(u'Administrator', invoice.primary_contact_last_name)

    def testGetNextFreeNumber(self):
        # No invoices in the database
        self.assertEquals(1, Invoice.objects.get_next_free_number())

        # At least one invoice in the database
        Invoice.objects.create(job_id=1, number=1, type=u'W',
            date=datetime.date.today(), amount_invoiced=123)
        self.assertEquals(2, Invoice.objects.get_next_free_number())
        Invoice.objects.create(job_id=1, number=2, type=u'W',
            date=datetime.date.today(), amount_invoiced=123)
        self.assertEquals(3, Invoice.objects.get_next_free_number())

        # Must be unaffected by larger numbers
        Invoice.objects.create(job_id=1, number=4, type=u'W',
            date=datetime.date.today(), amount_invoiced=123)
        self.assertEquals(3, Invoice.objects.get_next_free_number())
