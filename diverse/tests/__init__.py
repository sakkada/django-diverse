from django.core.files.base import ContentFile
#from django.test import TestCase
from django.db import models
from django.utils import unittest
import os, tempfile

from diverse.fields.fields import DiverseFileField, DiverseImageField
from diverse.processor.imagekit import ImageKit, Fit, Adjust

#from diverse.processors import BaseProcessor
#from diverse.files import VersionFile, ImageVersionFile
#from diverse.conveyor import TempFileConveyor
from diverse.version import Version, ImageVersion
from diverse.container import BaseContainer

UPLOAD_TO = u'diversetests'

class Container(BaseContainer):

    sample = ImageVersion(
        ImageKit(processors=[Adjust(sharpness=5.0), Fit(600, 600)], 
                 format='JPEG', options={'quality': 90},),
        lazy=False,
    )

    admin = ImageVersion(
        ImageKit(processors=[Fit(200, 200)], 
                 format='JPEG', options={'quality': 90},),
        lazy=True,
    )

class Sample(models.Model):
    image = DiverseImageField('image', blank=True, upload_to=UPLOAD_TO, 
                              container=Container, clearable=True, 
                              update_checkbox=True, thumbnail='admin',)
    image_cache = models.CharField('cache', max_length=10000, blank=True)

class DiverseTestCase(unittest.TestCase):
    def setUp(self):
        self.sample = Sample()
        image = self.generate_sample()
        cfile = ContentFile(image.read())
        self.sample.image = cfile
        self.sample.image.save('test.jpeg', cfile)
        self.sample.save(), image.close()

    def generate_sample(self):
        """sample taken from interfacelift.com"""
        from diverse.processors.imagekit.lib import Image

        filetemp = tempfile.TemporaryFile()
        samplepath = os.path.join(os.path.dirname(os.path.abspath(__file__)), 
                                  'samples', '02786_lakefornight_1024x768.jpg')
        with open(samplepath, "r+b") as samplefile:
            Image.open(samplefile).save(filetemp, 'JPEG')
        filetemp.seek(0)
        return filetemp

    def test_animals_can_speak(self):
        """Animals that can speak are correctly identified"""
        self.assertEqual(2, 1+1)

"""
from imagekit import utils
from imagekit.lib import Image
from imagekit.models import ImageSpec
from imagekit.processors import Adjust
from imagekit.processors.resize import Crop, SmartCrop


class Photo(models.Model):
    original_image = models.ImageField(upload_to='photos')
    
    thumbnail = ImageSpec([Adjust(contrast=1.2, sharpness=1.1), Crop(50, 50)],
            image_field='original_image', format='JPEG',
            options={'quality': 90})
    
    smartcropped_thumbnail = ImageSpec([Adjust(contrast=1.2, sharpness=1.1), SmartCrop(50, 50)],
            image_field='original_image', format='JPEG',
            options={'quality': 90})


class IKTest(TestCase):
    def generate_image(self):
        tmp = tempfile.TemporaryFile()
        Image.new('RGB', (800, 600)).save(tmp, 'JPEG')
        tmp.seek(0)
        return tmp
    
    def generate_lenna(self):
        " ""
        See also:
        
        http://en.wikipedia.org/wiki/Lenna
        http://sipi.usc.edu/database/database.php?volume=misc&image=12
        
        " ""
        tmp = tempfile.TemporaryFile()
        lennapath = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'assets', 'lenna-800x600-white-border.jpg')
        with open(lennapath, "r+b") as lennafile:
            Image.open(lennafile).save(tmp, 'JPEG')
        tmp.seek(0)
        return tmp
    
    def setUp(self):
        self.photo = Photo()
        img = self.generate_lenna()
        file = ContentFile(img.read())
        self.photo.original_image = file
        self.photo.original_image.save('test.jpeg', file)
        self.photo.save()
        img.close()
    
    def test_save_image(self):
        photo = Photo.objects.get(id=self.photo.id)
        self.assertTrue(os.path.isfile(photo.original_image.path))
    
    def test_setup(self):
        self.assertEqual(self.photo.original_image.width, 800)
        self.assertEqual(self.photo.original_image.height, 600)
    
    def test_thumbnail_creation(self):
        photo = Photo.objects.get(id=self.photo.id)
        self.assertTrue(os.path.isfile(photo.thumbnail.file.name))
    
    def test_thumbnail_size(self):
        " "" Explicit and smart-cropped thumbnail size "" "
        self.assertEqual(self.photo.thumbnail.width, 50)
        self.assertEqual(self.photo.thumbnail.height, 50)
        self.assertEqual(self.photo.smartcropped_thumbnail.width, 50)
        self.assertEqual(self.photo.smartcropped_thumbnail.height, 50)
    
    def test_thumbnail_source_file(self):
        self.assertEqual(
            self.photo.thumbnail.source_file, self.photo.original_image)


class IKUtilsTest(TestCase):
    def test_extension_to_format(self):
        self.assertEqual(utils.extension_to_format('.jpeg'), 'JPEG')
        self.assertEqual(utils.extension_to_format('.rgba'), 'SGI')

        with self.assertRaises(utils.UnknownExtensionError):
            utils.extension_to_format('.txt')

    def test_format_to_extension_no_init(self):
        self.assertEqual(utils.format_to_extension('PNG'), '.png')
        self.assertEqual(utils.format_to_extension('ICO'), '.ico')

        with self.assertRaises(utils.UnknownFormatError):
            utils.format_to_extension('TXT')

"""