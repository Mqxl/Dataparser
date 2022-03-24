from django.contrib import admin
from .models import *
# Register your models here.


class DataImageInline(admin.TabularInline):
    model = ImageFromParser
    extra = 3


class DataAdmin(admin.ModelAdmin):
    inlines = [DataImageInline, ]


admin.site.register(DataFromParser, DataAdmin)