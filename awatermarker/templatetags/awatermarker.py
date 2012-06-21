from django import template
from django.conf import settings
from photo_videos.storage import get_upload_storage
from django.utils.safestring import mark_safe
from django.core.cache import cache

register = template.Library()

@register.simple_tag
def watermark(url):
    if not settings.SITE_ID == 1:
        return url
    image_url = url.split("?")[0]
    filename = "{0}.{1}".format(image_url, settings.DEFAULT_WATERMARK_SLUG)
    if not filename.startswith(settings.S3_BUCKET_URL):
        return filename

    cache_key = "watermark-%s" % filename
    cache_key = cache_key.strip()
    cached_val = cache.get(cache_key)
    if cached_val:
        return cached_val
    storage = get_upload_storage(delayed=True).remote
    new_url = storage.url(filename.replace(settings.S3_BUCKET_URL, ""))
    cache.set(cache_key, new_url, settings.WATERMARK_URL_CACHE_TIME)
    return new_url


