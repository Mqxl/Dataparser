import urllib.request, urllib.parse, urllib.error
import random
import string
from pathlib import Path

from django.core.files.storage import FileSystemStorage
from django.shortcuts import render
from bs4 import BeautifulSoup
from .models import *
from wsgiref.util import FileWrapper
import zipfile, requests
from django.http import HttpResponse
import json
# Create your views here.


def index(request):
    parseddata = DataFromParser.objects.filter(author=request.user)
    if request.GET.get('downloadimage'):
        projects = DataFromParser.objects.get(id=request.GET.get('downloadimage'))
        image_list = projects.images.all()
        with zipfile.ZipFile('export.zip', 'w') as export_zip:
            for i in image_list:
                export_zip.write(i.image.path, i.image.name)
        wrapper = FileWrapper(open('export.zip', 'rb'))
        content_type = 'application/zip'
        content_disposition = 'attachment; filename=export.zip'
        response = HttpResponse(wrapper, content_type=content_type)
        response['Content-Disposition'] = content_disposition
        return response
    if request.GET.get('downloadjson'):
        projects = DataFromParser.objects.get(id=request.GET.get('downloadjson'))
        with open('downloadjson.json', 'w') as jsonfile:
            json.dump(projects.parsedjson, jsonfile)
        wrapper = FileWrapper(open('export.json', 'rb'))
        content_type = 'application/json'
        content_disposition = 'attachment; filename=export.json'
        response = HttpResponse(wrapper,content_type=content_type)
        response['Content-Disposition'] = content_disposition
        return response
    if request.GET.get('downloadtext'):
        projects = DataFromParser.objects.get(id=request.GET.get('downloadtext'))
        response = HttpResponse(content_type='text/plain')
        response['Content-Disposition'] = 'attachment; filename="export.txt"'
        response.write((projects.parsedtext))
        return response
    return render(request, 'index.html', {"parseddata":parseddata})


def download_track(count, track_element, parserid):
    # Get the title of the track from the HTML element
    BASE_DIR = Path(__file__).resolve().parent.parent
    track_title = track_element.text.strip().replace('/', '-')
    download_url = '{}'.format(track_element['src'])
    letters = string.ascii_lowercase
    file_name = '{}/{}_{}{}.jpg'.format(os.path.join(BASE_DIR, 'parsedimage'),parserid.author,count, track_title + ''.join(random.choice(letters) for i in range(10)))

    # Download the track
    r = requests.get(download_url, allow_redirects=True)
    saveimage = ImageFromParser()
    letters = string.ascii_lowercase
    with open(file_name, 'wb') as f:
        f.write(r.content)
        saveimage.property = parserid
        saveimage.image = file_name
        saveimage.save()

def imageparser(request):
    if request.GET.get('Next') == 'Next':
        url = request.GET.get('url')
        r = requests.get(url)
        soup = BeautifulSoup(r.text, 'lxml')
        images = soup.findAll('img')
        saved = DataFromParser()
        if request.method == 'POST':
            saved.author = request.user
            saved.save()
            tracks = soup.findAll('img')
            count = 0
            for track in tracks:
                download_track(count, track, saved)
                count += 1
        return render(request, 'imageparser.html', {'image': [img['src'] for img in images]})
    return render(request, 'imageparser.html')


def textparser(request):
    if request.GET.get('Next') == 'Next':
        try:
            url = request.GET.get('url')
            r = requests.get(url)
            soup = BeautifulSoup(r.text, 'lxml')
            rate = soup.findAll()
            if request.method == 'POST':
                saved = DataFromParser()
                saved.parsedtext = rate
                saved.author = request.user
                saved.save()
            return render(request, 'textparser.html', {'url': rate})
        except:
            text = 'Error404|Dont have text to parse'
            return render(request, 'textparser.html', {'text': text})
    return render(request, 'textparser.html')


def jsonparser(request):
    if request.GET.get('Next') == 'Next':
        try:
            url = request.GET.get('url')
            data = urllib.request.urlopen(url).read()
            json_data = json.loads(data)
            if request.method == 'POST':
                saved = DataFromParser()
                saved.parsedjson = json_data
                saved.author = request.user
                saved.save()
            return render(request, 'jsonparser.html', {'url': json_data})
        except:
            text = 'Error404|Dont have json to parse'
            return render(request, 'jsonparser.html',{'text':text})
    return render(request, 'jsonparser.html')