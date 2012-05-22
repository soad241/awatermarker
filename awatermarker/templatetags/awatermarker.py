from django import template
from django.conf import settings
register = template.Library()

@register.simple_tag
def watermark(url):
    image_url = url.split("?")[0]
    params = url.split("?")[1]
    return "{0}.{1}?{2}".format(image_url,
                                settings.DEFAULT_WATERMARK_SLUG, params)
