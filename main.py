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
from io import open

options = Options()
options.add_argument("--headless")
PATH = "C:\Program Files (x86)\chromedriver.exe"
browser = webdriver.Chrome(PATH, chrome_options=options)

browser.get("https://namu.wiki/w/%EB%B6%84%EB%A5%98:%EB%8C%80%ED%95%9C%EB%AF%BC%EA%B5%AD%EC%9D%98%20%EC%A7%81%EC%97%85%EB%B3%84%20%EC%9D%B8%EB%AC%BC")

root = browser.find_elements_by_css_selector(".cl a")
leaf_selector = ".cl:nth-child(3) .c ul li a"
leaf_next_selector = ".cl:nth-child(3) a:nth-child(2)"
image_selector = ".w span span img:nth-child(2)"

def is_face(link):
    hdr = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.11 (KHTML, like Gecko) Chrome/23.0.1271.64 Safari/537.11',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.3',
        'Accept-Encoding': 'none',
        'Accept-Language': 'en-US,en;q=0.8',
        'Connection': 'keep-alive'}
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
    try:
        WebDriverWait(browser, 3).until(EC.presence_of_element_located((By.CSS_SELECTOR, image_selector)))
        images = browser.find_elements_by_css_selector(image_selector)
        for image in images:
            image_src = image.get_attribute("src")
            
            response = requests.get(image_src.strip())

            im = Image.open(BytesIO(response.content))
            width, height = im.size
            if(width > 256 and height > 256 and height > width and is_face(image_src)):
                return image_src

    except (NoSuchElementException, TimeoutException):
        return ''

def get_href(l):
    for i, link in enumerate(l):
        l[i] = {"title":link.text , "url": link.get_attribute("href").strip()}
    return l

root = get_href(root)

def get_leaf_href():
    leaf_urls = browser.find_elements_by_css_selector(leaf_selector)
    leaf_urls = get_href(leaf_urls)
    try:
        has_next = True
        while(has_next):
            try:
                leaf_next = browser.find_element_by_css_selector(leaf_next_selector)
                browser.get(leaf_next.get_attribute('href'))
                leaf_urls += get_href(browser.find_elements_by_css_selector(leaf_selector))
            except InvalidArgumentException:
                has_next = False

    except NoSuchElementException:
        leaf_urls = browser.find_elements_by_css_selector(leaf_selector)
        return get_href(leaf_urls)
    return leaf_urls

def get_leaf():
    leaf_links = get_leaf_href()
    leaf_docs = []
    for leaf_link in leaf_links:
        index = leaf_link['title'].find("(") if leaf_link['title'].find("(") > 0 else len(leaf_link['title'])
        if(len(leaf_link['title'][:index].encode("utf-8")) >= 12): continue
        browser.get(leaf_link['url'])
        content = get_content(leaf_link)
        if(content['image'] is None): continue
        leaf_docs.append(content)

    return leaf_docs

def get_content(link):
    print(link['url'])
    if(not link['title'].find("/") == -1): return {"image": None}
    browser.get(link['url'])
    image = get_image(link['url'])
    
    return {
        "title": link['title'],
        "image": image
    }
link_tree = []
for item in root:
    browser.get(item['url'])
    sub_links_selector = browser.find_elements_by_css_selector(".cl:nth-child(2) .c a")
    sub_links = get_href(sub_links_selector)
    
    leaf = get_leaf()
    
    link_sub_tree = []
    for sub_link in sub_links:
        browser.get(sub_link['url'])
        sub_leaf = get_leaf()
        sub_sub_links = browser.find_elements_by_css_selector(".cl:nth-child(2) a")
        sub_sub_links = get_href(sub_sub_links)
        
        link_sub_sub_tree = []
        for sub_sub_link in sub_sub_links:
            content = get_content(sub_sub_link)
            link_sub_sub_tree.append(content)
        
        link_sub_tree.append({
            "title": sub_link['title'],
            "leaf_docs": sub_leaf,
            "sub": link_sub_sub_tree
        })

    link_tree.append({
        "title": item['title'],
        "leaf_docs": leaf,
        "sub": link_sub_tree
    })
    with open(u"{}.json".format(sub_link['title']), 'w', encoding="utf8") as json_file:
        data = json.dumps(link_sub_tree, indent = 2, ensure_ascii = False)
        json_file.write(unicode(data))
    