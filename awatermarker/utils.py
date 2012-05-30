import os
import Image, ImageEnhance
from django.conf import settings
from mystorage.util import get_upload_storage
from django.core.files.base import ContentFile    
try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO

QUALITY = getattr(settings, 'WATERMARKING_QUALITY', 85)
OBSCURE = getattr(settings, 'WATERMARK_OBSCURE_ORIGINAL', True)
RANDOM_POS_ONCE = getattr(settings, 'WATERMARK_RANDOM_POSITION_ONCE', True)
ROTATION = getattr(settings, 'WATERMARK_ROTATION', 0)
POSITION = getattr(settings, 'WATERMARK_POSITION', "br")
OBSCURE = getattr(settings, 'WATERMARK_OBSCURE', True)

def determine_scale(scale, img, mark):
    if scale:
        try:
            scale = float(scale)
        except (ValueError, TypeError):
            pass

        if type(scale) in (str, unicode) and scale.lower() == 'f':
            # scale, but preserve the aspect ratio
            scale = min(
                        float(img.size[0]) / mark.size[0],
                        float(img.size[1]) / mark.size[1]
                       )
        elif type(scale) not in (float, int):
            raise ValueError('Invalid scale value "%s"!  Valid values are 1) "F" for ratio-preserving scaling and 2) floating-point numbers and integers greater than 0.' % (scale,))

        # determine the new width and height
        w = int(mark.size[0] * float(scale))
        h = int(mark.size[1] * float(scale))

        # apply the new width and height, and return the new `mark`
        return (w, h)
    else:
        return mark.size


def determine_position(position, img, mark):
    max_left = max(img.size[0] - mark.size[0], 0)
    max_top = max(img.size[1] - mark.size[1], 0)
    if not position:
        position = 'r'
    if isinstance(position, tuple):
        left, top = position
    elif isinstance(position, str) or isinstance(position, unicode):
        position = position.lower()
        # corner positioning
        if position in ['tl', 'tr', 'br', 'bl']:
            if 't' in position:
                top = 0
            elif 'b' in position:
                top = max_top
            if 'l' in position:
                left = 0
            elif 'r' in position:
                left = max_left
        # center positioning
        elif position == 'c':
            left = int(max_left / 2)
            top = int(max_top / 2)
        # random positioning
        elif position == 'r':
            left = random.randint(0, max_left)
            top = random.randint(0, max_top)
        # relative or absolute positioning
        elif 'x' in position:
            left, top = position.split('x')
            if '%' in left:
                left = max_left * _percent(left)
            else:
                left = _int(left)
            if '%' in top:
                top = max_top * _percent(top)
            else:
                top = _int(top)
    return (left, top)

def reduce_opacity(img, opacity):
    """
    Returns an image with reduced opacity.
    """
    assert opacity >= 0 and opacity <= 1
    if img.mode != 'RGBA':
        img = img.convert('RGBA')
    else:
        img = img.copy()
    alpha = img.split()[3]
    alpha = ImageEnhance.Brightness(alpha).enhance(opacity)
    img.putalpha(alpha)
    return img

def generate_watermarks(image_name, storage):
    """ Generates all watermarks for the given image """
    img = Image.open(storage.open(image_name))
    for mark_name in settings.ALL_WATERMARK_LIST:
        mark = Image.open(settings.MEDIA_ROOT+mark_name[0])
        sufix = mark_name[1]
        position = determine_position(POSITION, img, mark)
        rotation = ROTATION
        scale = 1.0
        opacity = 1.0
        tile = False
        scale = 1.0
        greyscale = False
        obscure = OBSCURE
        quality = QUALITY

        basedir = '%s/watermarked' % os.path.dirname(image_name)
        base, ext = os.path.splitext(os.path.basename(image_name))
        pos = determine_position(position, img, mark)
        params = {
            'position':  position,
            'opacity':   opacity,
            'scale':     scale,
            'tile':      tile,
            'greyscale': greyscale,
            'rotation':  rotation,
            'base':      base,
            'ext':       ext,
            'quality':   quality,
            'watermark': sufix,
            'opacity_int': int(opacity * 100),
            'left':      pos[0],
            'top':       pos[1],
        }

        wm_name = sufix        
        if opacity < 1:
            mark = reduce_opacity(mark, opacity)
        scale = determine_scale(scale, img, mark)
        mark = mark.resize(scale)
        if greyscale and mark.mode != 'LA':
            mark = mark.convert('LA')
        layer = Image.new('RGBA', img.size, (0,0,0,0))
        if tile:
            first_y = position[1] % mark.size[1] - mark.size[1]
            first_x = position[0] % mark.size[0] - mark.size[0]

            for y in range(first_y, img.size[1], mark.size[1]):
                for x in range(first_x, img.size[0], mark.size[0]):
                    layer.paste(mark, (x, y))
        else:
            layer.paste(mark, position)

        # composite the watermark with the layer
        composed_image =  Image.composite(layer, img, layer)
        memory_file = StringIO()
        composed_image.save(memory_file, quality=quality, format="jpeg")
        cf = ContentFile(memory_file.getvalue())
        filename = "{0}.{1}".format(image_name,sufix)
        storage.save(filename, cf)





        
