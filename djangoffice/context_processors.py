from django.conf import settings
from django.utils.safestring import mark_safe

def app_constants(request):
    """
    Returns context variables which contain information about the
    application and the client.
    """
    return {
        'COMPANY_NAME':        mark_safe(settings.COMPANY_NAME),
        'APPLICATION_NAME':    mark_safe(settings.APPLICATION_NAME),
        'APPLICATION_VERSION': mark_safe(settings.APPLICATION_VERSION),
    }
