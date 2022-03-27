from logging import exception
from tkinter import Image
import urllib.request, urllib.parse, urllib.error
import random
import string
from pathlib import Path
import instaloader
import csv
from django.shortcuts import get_object_or_404, redirect, render
from bs4 import BeautifulSoup
from .models import *
from wsgiref.util import FileWrapper
import zipfile, requests
from django.http import HttpResponse
import json
import vk
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout as auth_logout
# Create your views here.

@login_required
def index(request):
    parseddata = DataFromParser.objects.filter(author=request.user)
    image_list = []
    for i in parseddata:
        try:
            pars = DataFromParser.objects.get(id=i.id)
            img = pars.images.all()
            for i in img:
                image_list.append(i)
        except:
            continue
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
    return render(request, 'dashboard/dashboard.html', {"parseddata":parseddata,"js":[i.createdate.month for i in parseddata],'image_list':image_list})


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
        try:
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
            return render(request, 'dashboard/imageparser.html', {'image': [img['src'] for img in images]})
        except:
            text = 'Error404|Dont have image or error'
            return render(request, 'dashboard/imageparser.html', {'text': text})
    return render(request, 'dashboard/imageparser.html')


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
            return render(request, 'dashboard/textparser.html', {'url': rate})
        except:
            text = 'Error404|Dont have text to parse'
            return render(request, 'dashboard/textparser.html', {'text': text})
    return render(request, 'dashboard/textparser.html')


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
            return render(request, 'dashboard/jsonparser.html', {'url': json_data})
        except:
            text = 'Error404|Dont have json to parse'
            return render(request, 'dashboard/jsonparser.html',{'text':text})
    return render(request, 'dashboard/jsonparser.html')

def instagramparser(request):
    if request.GET.get('Next') == 'Next':
        try:
            url = request.GET.get('url')
            L = instaloader.Instaloader()
            L.login(request.GET.get('login'), request.GET.get('password'))
            Post = instaloader.Post.from_shortcode(L.context, url)
            f = open('test.csv', 'w')
            csvwt = csv.writer(f)
            for like in Post.get_likes():
                csvwt.writerow("Username:",[like.username, like.external_url])
            f.close()
            return render(request, 'dashboard/instagramparser.html',{'data': [i.username for i in Post.get_likes()]})
        except:
            text = 'Error404|Dont have instapost to parse'
            return render(request, 'dashboard/instagramparser.html',{'text':text})
    return render(request, 'dashboard/instagramparser.html')

def get_members(groupid):
    token = "841452f6841452f6841452f645847fa55b88414841452f6d92b959cd504ad2f8d977137"
    session = vk.Session(access_token=token)
    vk_api = vk.API(session)
    first = vk_api.groups.getMembers(group_id=groupid, v=5.92)  # Первое выполнение метода
    data = first["items"]  # Присваиваем переменной первую тысячу id'шников
    count = first["count"] // 1000  # Присваиваем переменной количество тысяч участников
    # С каждым проходом цикла смещение offset увеличивается на тысячу
    # и еще тысяча id'шников добавляется к нашему списку.
    for i in range(1, count+1):  
        data = data + vk_api.groups.getMembers(group_id=groupid, v=5.92, offset=i*1000)["items"]
    return data

def save_data(data, filename="data.txt"):  # Функция сохранения базы в txt файле
    with open(filename, "w") as file:  # Открываем файл на запись
        # Записываем каждый id'шник в новой строке,
        # добавляя в начало "vk.com/id", а в конец перенос строки.
        for item in data:   
            file.write("vk.com/id" + str(item) + "\n") 


def enter_data(filename="data.txt"):  # Функция ввода базы из txt файла
    with open(filename) as file:  # Открываем файл на чтение
        b = [] 
        # Записываем каждую строчку файла в список,
        # убирая "vk.com/id" и "\n" с помощью среза.
        for line in file:   
            b.append(line[9:len(line) - 1])  
    return b

def vkparser(request):
    if request.GET.get('Next') == 'Next':
        try:
            url = request.GET.get('url')
            bobfilm = get_members(url)
            save_data(bobfilm)
            return render(request, 'dashboard/vkparser.html',{'data': bobfilm})
        except:
            text = 'Error404|Write vk group id'
            return render(request, 'dashboard/vkparser.html',{'text':text})
    return render(request, 'dashboard/vkparser.html')

def logout(request):
    auth_logout(request)
    return redirect('/')