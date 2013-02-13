# based on django-imagekit source code
# diff: code is completely original
#       text formatting changed

# Required PIL classes may or may not be available from the root namespace
# depending on the installation method used.
try:
    from PIL import Image, ImageColor, ImageChops, ImageEnhance, \
                    ImageFile, ImageFilter, ImageDraw, ImageStat
except ImportError:
    try:
        import Image, ImageColor, ImageChops, ImageEnhance, \
               ImageFile, ImageFilter, ImageDraw, ImageStat
    except ImportError:
        raise ImportError('ImageKit was unable to import the Python Imaging Library. Please'
                          ' confirm it`s installed and available on your current Python path.')

try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO