#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Oct  4 14:37:06 2022

@author: mpalerme

module to init database
"""

import sqlite3
import requests
from bs4 import BeautifulSoup as BfS
import re
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait


ADDR_FIREFOX = "https://www.mozilla.org/en-US/firefox/releases/"
ADDR_CHROME = "https://chromereleases.googleblog.com/search/label/Desktop%20Update"
ADDR_EDGE = "https://learn.microsoft.com/en-us/deployedge/microsoft-edge-release-schedule"
ADDR_SAFARI = "https://developer.apple.com/documentation/safari-release-notes"

# Create data base
conn = sqlite3.connect('ma_base.db')


cursor = conn.cursor()
cursor.execute("""
CREATE TABLE IF NOT EXISTS browser(
     id INTEGER PRIMARY KEY AUTOINCREMENT UNIQUE,
     name TEXT,
     version INTEGER
)
""")
cursor.execute("""
CREATE TABLE IF NOT EXISTS my_user(
     login VARCHAR(20) PRIMARY KEY UNIQUE NOT NULL,
     email VARCHAR(50) UNIQUE NOT NULL,
     pwd VARCHAR(50),
     status ENUM('', 'super', 'temp', 'temp_super')
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS input(
     uuid VARCHAR(40) PRIMARY KEY UNIQUE,
     login VARCHAR(20) NOT NULL,
     size INTERGER,
     state INTERGER,
     upload DATETIME NOT NULL,
     update DATETIME,
     options VARCHAR(100)
     FOREIGN KEY(login) REFERENCES my_user(login)
)
""")
conn.commit()

###### Get last version of browsers

### Firefox
req = requests.get(ADDR_FIREFOX)

# Parsing the HTML
page = BfS(req.content, 'html.parser')

# work on release part
release_part = page.find('ol', class_='c-release-list')

# take first link
link = release_part.find('a')

version = int(link.text.split('.')[0]) - 1

cursor.execute("""
INSERT INTO browser(name, version) VALUES(?, ?)""", ("Firefox", version))

conn.commit()

### Chrome
req = requests.get(ADDR_CHROME)

# Parsing the HTML
page = BfS(req.content, 'html.parser')

# work on release part
release_part = page.find_all('div', class_='post')

for post in release_part:
    if 'Stable' in post.find('a').text:
        # Extract complete version
        version = re.findall('[0-9]*\.[0-9]*\.[0-9]*\.[0-9]*', post.text)[0]
        # main previous version
        version = int(version.split('.')[0]) - 1
        break


cursor.execute("""
INSERT INTO browser(name, version) VALUES(?, ?)""", ("Chrome", version))

conn.commit()

### Edge
req = requests.get(ADDR_EDGE)

# Parsing the HTML
page = BfS(req.content, 'html.parser')

# work on release part
release_part = page.find_all('table')

for table in release_part:
    if table.find('th', string='Version'):
       break

# take all links
links = table.find_all('a')

# Find last stable version
for index in range(len(links)):
    if 'stable' in links[-(index + 1)].get('href'):
        version = int(links[-(index + 1)].text.split('.')[0]) - 1
        break

cursor.execute("""
INSERT INTO browser(name, version) VALUES(?, ?)""", ("Edge", version))

conn.commit()

### Safari
op_fire = Options()
op_fire.add_argument('--headless')
driver = webdriver.Firefox(options=op_fire)
driver.get(ADDR_SAFARI)
version = WebDriverWait(driver, timeout=3).until(lambda d: d.find_element(By.CLASS_NAME,"highlight"))
version = version.text
driver.quit()
version = version.split()[1]
version = int(version) - 1

cursor.execute("""
INSERT INTO browser(name, version) VALUES(?, ?)""", ("Safari", version))

conn.commit()

conn.close()
