from django import template
from django.conf import settings
from storages.backends.s3boto import S3BotoStorage
from photo_videos.storage import get_upload_storage
from django.utils.safestring import mark_safe

register = template.Library()

@register.simple_tag
def watermark(url):
    if not settings.SITE_ID == 1:
        return url
    image_url = url.split("?")[0]
    params = url.split("?")[1]
    filename = "{0}.{1}".format(image_url, settings.DEFAULT_WATERMARK_SLUG)
    st = get_upload_storage()
    filename = filename.replace(settings.UPLOAD_MEDIA_URL, "")
    filename = filename.replace(settings.S3_BUCKET_URL, "")
    if st.get_storage(filename) == st.remote:
        storage = S3BotoStorage()
        return mark_safe(storage.url(filename))
    return mark_safe(settings.UPLOAD_MEDIA_URL + filename)



