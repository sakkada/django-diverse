# based on django-imagekit source code
# based on version (1.1.0 dev 0)
from processors import Adjust, Reflection, Transpose, resize
from processors.resize import Crop, Fit, SmartCrop
from processor import ImageKit