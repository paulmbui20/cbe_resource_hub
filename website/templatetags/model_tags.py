from django import template

register = template.Library()

@register.simple_tag
def get_obj_attr(obj, attr_name):
    """
    Dynamically access models properties in generic list templates to keep templates fully DRY.
    Usage: {% get_obj_attr obj "field_name" as val %}
    """
    try:
        val = getattr(obj, attr_name)
        if callable(val):
            return val()
        return val
    except AttributeError:
        return ""
