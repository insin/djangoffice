from django import template

register = template.Library()

########
# Tags #
########

class NumberFieldForJobNode(template.Node):
    def __init__(self, job, form, context_var):
        self.job = job
        self.form = form
        self.context_var = context_var

    def render(self, context):
        try:
            form = template.resolve_variable(self.form, context)
            job = template.resolve_variable(self.job, context)
        except template.VariableDoesNotExist:
            return u''
        context[self.context_var] = form.__getitem__(u'number%s' % job.id)
        return u''

@register.tag('number_field_for_job')
def do_number_field_for_job(parser, token):
    """
    Looks up a bound number field for a given Job in a given Form an
    stores it in a context variable.

    Example usage::

        {% number_field_for_job job from form as field %}
    """
    bits = token.contents.split()
    if len(bits) != 6:
        raise template.TemplateSyntaxError("'%s' tag takes exactly five arguments" % bits[0])
    if bits[2] != 'from':
        raise template.TemplateSyntaxError("second argument to '%s' tag must be 'from'" % bits[0])
    if bits[4] != 'as':
        raise template.TemplateSyntaxError("fourth argument to '%s' tag must be 'as'" % bits[0])
    return NumberFieldForJobNode(bits[1], bits[3], bits[5])
