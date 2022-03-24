import os
from urllib.request import urlopen
from django.core.files import File
from django.core.files.temp import NamedTemporaryFile
from django.db import models
from django.contrib.auth.models import User
# Create your models here.


class DataFromParser(models.Model):
    createdate = models.DateTimeField(auto_now_add=True)
    parsedtext = models.TextField(max_length=5000, null=True, blank=True)
    parsedjson = models.JSONField(null=True, blank=True)
    author = models.ForeignKey(User, to_field="username", on_delete=models.DO_NOTHING,blank=True)


class ImageFromParser(models.Model):
    property = models.ForeignKey(DataFromParser, related_name='images', on_delete=models.CASCADE)
    image = models.ImageField()

    def get_image_from_url(self, url, property):
        img_tmp = NamedTemporaryFile()
        with urlopen(url) as uo:
            assert uo.status == 200
            img_tmp.write(uo.read())
            img_tmp.flush()
        img = File(img_tmp)
        self.image.save(img_tmp.name, img)
        self.image_url = url
        self.property = property