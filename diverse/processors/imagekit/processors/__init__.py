# based on django-imagekit source code
# diff: whole module code is completely original except
#       import section fixes of required files
#       base, resize, utils: imagekit.lib -> ..lib, ect;
#       text formatting as preserved (as possible)

"""
Imagekit image processors.

A processor accepts an image, does some stuff, and returns the result.
Processors can do anything with the image you want, but their responsibilities
should be limited to image manipulations--they should be completely decoupled
from both the filesystem and the ORM.

"""

from .base import *
from .crop import *
from .resize import *
