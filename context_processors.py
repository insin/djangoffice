from django.conf import settings

def app_constants(request):
    """
    Returns context variables which contain information about the
    application and the client.
    """
    return {
        'COMPANY_NAME':        settings.COMPANY_NAME,
        'APPLICATION_NAME':    settings.APPLICATION_NAME,
        'APPLICATION_VERSION': settings.APPLICATION_VERSION,
    }
