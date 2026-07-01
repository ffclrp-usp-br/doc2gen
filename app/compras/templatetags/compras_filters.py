from django import template
import os

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


@register.filter(name='filename')
def filename(value):
    """
    Returns the filename from a file path.
    Example: 'modelos_oficiais/CONFERENCIA_PREGAO.docx' -> 'CONFERENCIA_PREGAO.docx'
    """
    if value is None:
        return ""
    return os.path.basename(str(value))
