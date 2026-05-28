from django import template

register = template.Library()

@register.filter(name='moeda')
def moeda(value):
    """
    Formats a decimal or float value to Brazilian Real currency format (e.g. R$ 972.292,80).
    """
    if value is None or value == '':
        return ""
    try:
        val = float(value)
        return f"R$ {val:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except (ValueError, TypeError):
        return value
