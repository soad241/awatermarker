from django import template
from django.conf import settings
register = template.Library()
from storages.backends.s3boto import S3BotoStorage

@register.simple_tag
def watermark(url):
    if not settings.SITE_ID == 1:
        return url
    image_url = url.split("?")[0]
    params = url.split("?")[1]
    filename = "{0}.{1}".format(image_url, settings.DEFAULT_WATERMARK_SLUG)
    filename = filename.replace(settings.S3_BUCKET_URL, "")
    storage = S3BotoStorage()
    return storage.url(filename)



