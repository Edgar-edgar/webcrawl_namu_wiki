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

def fact(n):
    if(n == 0): return 1
    

res = fact(5)
print(res)