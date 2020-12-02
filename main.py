# encoding: utf-8

from cv2 import cv2
from selenium import webdriver
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException, TimeoutException, InvalidArgumentException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
import requests
from io import BytesIO
import time, webbrowser
from PIL import Image
import numpy as np
import urllib2
import json
import random
from PyJSONSerialization import dump
import os
from dotenv import load_dotenv
from io import open
load_dotenv()

options = Options()
options.add_argument("--headless")
PATH = os.environ.get('WEBDRIVER_PATH')
browser = webdriver.Chrome(PATH, chrome_options=options)

content_selector = ".cl:nth-child(3) .c ul li a"
leaf_next_selector = ".cl:nth-child(3) a:nth-child(2)"
image_selector = ".w span span img:nth-child(2)"

hdr = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.11 (KHTML, like Gecko) Chrome/23.0.1271.64 Safari/537.11',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.3',
    'Accept-Encoding': 'none',
    'Accept-Language': 'en-US,en;q=0.8',
    'Connection': 'keep-alive'}

history = []
class Tree:
    def __init__(self, title):
        self.title = title
        self.sub = []

    def addChild(self, tree):
        if(isinstance(tree, Tree) or type(tree) is dict): self.sub.append(tree)
        else: self.sub += tree

    def setChild(self, sub):
        self.sub = sub

def get_root_json():
    with open('json/root.json', 'r', encoding="utf8") as json_file:
        return json.loads(json_file.read())

def random_sleep(a,b):
    start = random.randrange(a,b)
    time.sleep(start)

def is_done(directory):
    for h in history:
        if(directory['url'] == h['url']):
            return True
    return False
    
def redirect(directory):
    browser.get(directory['url'])
    history.append(directory)
    random_sleep(1,4)

def save_json(path, data):
    with open(u'json/{}'.format(path), 'w', encoding="utf8") as json_file:
        json_file.write(unicode(data))

def is_face(link):
    resp = urllib2.Request(link, headers=hdr)
    try:
        page = urllib2.urlopen(resp)
    except urllib2.HTTPError:
        print("error")
    
    has_face = False
    arr = np.asarray(bytearray(page.read()), dtype=np.uint8)
    image = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    image = cv2.imdecode(arr, -1)
    
    try:
        image = cv2.imread(image)
    except: pass

    if(image is None): return
    image = cv2.cvtColor(image, cv2.COLOR_RGBA2BGRA)
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    cascades = [
        {"type": "haarcascade_eye.xml", "scale": 2.5, "neighbors": 2, "color":(255,0,0)},
        {"type": "haarcascade_frontalface_default.xml", "scale": 1.5, "neighbors": 2, "color":(0,244,0) },
    ]

    for cascade in cascades:
        classifier = cv2.CascadeClassifier(cascade["type"])
        feature = classifier.detectMultiScale(gray, cascade['scale'], cascade['neighbors'])
        
        for (x,y,w,h) in feature:
            cv2.rectangle(image, (x,y) , (x+w, y+h), cascade['color'], 4 )
            has_face = True
            
    return has_face
    
def get_image(link):
    message = 'No image'
    try:
        WebDriverWait(browser, 3).until(EC.presence_of_element_located((By.CSS_SELECTOR, image_selector)))
        images = browser.find_elements_by_css_selector(image_selector)
        for image in images:
            image_src = image.get_attribute("src")
            
            response = requests.get(image_src.strip())
            try:
                im = Image.open(BytesIO(response.content))
            except IOError:
                continue

            width, height = im.size

            if(width < 256 and height < 256 and height < width): 
                message = 'Invalid image(too small). Crawled with an empty image field.'
                continue
            if(is_face(image_src)): 
                message = image_src
                break

            else: message = 'Image does not contain any faces.'
        return message
            
    except (NoSuchElementException, TimeoutException):
        return message

def get_href(l):
    nl = []
    for link in l:
        if link.text.strip() == 'Prev' or link.text.strip() == 'Next' or link.get_attribute("href") is None: continue
        nl.append({ "title": link.text , "url": link.get_attribute("href").strip() })
    return nl

def get_urls(text):
    containers = browser.find_elements_by_css_selector('.cl')
    content_urls = []
    for container in containers:
        header = container.find_element_by_css_selector('.wiki-heading')
        if(header.text.find(text) == -1): continue
        content_urls = container.find_elements_by_css_selector('a')
        break

    return get_href(content_urls)

def get_content_href(urls = None):
    if urls is None: urls = []

    urls += get_urls(u'분류에 속하는 문서')

    try:
        leaf_next = browser.find_element_by_css_selector(leaf_next_selector)
        browser.get(leaf_next.get_attribute('href'))
    except (InvalidArgumentException, NoSuchElementException):
        return urls

    return get_content_href(urls)

def get_item(link):
    redirect(link)
    image = get_image(link['url'])
    
    return {
        "title": link['title'],
        "image": image
    }

def get_content():
    content_links = get_content_href([])
    content_docs = []
    for content_link in content_links:
        if(content_link['title'].find("/") > -1): continue
        index = content_link['title'].find("(") if content_link['title'].find("(") > 0 else len(content_link['title'])
        if(len(content_link['title'][:index].encode("utf-8")) > 12): continue
        redirect(content_link)

        item = get_item(content_link)
        content_docs.append(item)

    return content_docs

def crawl(directory, tree, depth):
    start = time.time()
    if depth > 0:
        if(is_done(directory)): return tree
        redirect(directory)
        directories = get_urls(u'하위 분류')
        for d in directories:
            content = get_content()
            t = Tree(d['title'])
            if len(content) > 0: t.setChild(content)
            child = crawl(d, t, depth-1)
            if(len(child.sub) > 0): tree.addChild(child)
        
        redirect(directory)
        content = get_content()
        for page in content:
            if(directory['title'] == page['title']):
                tree.setChild(page)
                return tree
        if len(content) > 0 and len(directories) < 1: tree.setChild(content)
        elif len(content) > 0: tree.addChild(content)
        return tree
    print('Time elapsed for {}: {}'.format(directory['url'], str(time.time() - start)))
    return tree

root = get_root_json()
depth = 2
for i in range(1,30):
    data = crawl(root[i], Tree(root[i]['title']), depth)
    save_json(u'{}.json'.format(root[i]['title']), dump(data))
