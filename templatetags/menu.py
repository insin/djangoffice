from django import template

from officeaid.menu import build_menu_items

register = template.Library()

@register.inclusion_tag('menu.html', takes_context=True)
def menu(context, section=None, page=None):
    """
    Display section and current section (if any) page menus.

    Sample usage::

        {% menu "some_section" %}
        {% menu "some_section" "some_page" %}
    """
    section_items, page_items = build_menu_items(context['user'], section, page)
    return {
        'user': context['user'],
        'section': section,
        'section_items': section_items,
        'page': page,
        'page_items': page_items,
    }
