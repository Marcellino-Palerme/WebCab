#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Oct  4 14:37:06 2022

@author: mpalerme

module to init database
"""
import sys
import os
import requests
from bs4 import BeautifulSoup as BfS
import re
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait

sys.path.append(os.path.dirname(__file__))
from connect import connect_dbb

def init_base():
    """
    Initialise the database

    Returns
    -------
    None.

    """
    ADDR_FIREFOX = "https://www.mozilla.org/en-US/firefox/releases/"
    ADDR_CHROME = "https://chromereleases.googleblog.com/search/label/Desktop%20Update"
    ADDR_EDGE = "https://learn.microsoft.com/en-us/deployedge/microsoft-edge-release-schedule"
    ADDR_SAFARI = "https://developer.apple.com/documentation/safari-release-notes"

    # Connect to data base
    cursor = connect_dbb()

    # Create all tables
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS browser(
         id SERIAL PRIMARY KEY UNIQUE,
         name TEXT,
         version INTEGER
    )
    """)
    cursor.execute("""CREATE TYPE status_type AS
                      ENUM ('', 'super', 'temp', 'temp_super')""")

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS my_user(
         login VARCHAR(20) PRIMARY KEY UNIQUE NOT NULL,
         email VARCHAR(50) UNIQUE NOT NULL,
         pwd VARCHAR(50),
         status status_type
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS inputs(
         uuid VARCHAR(40) PRIMARY KEY UNIQUE,
         login VARCHAR(20) NOT NULL,
         size INTERGER,
         state INTERGER,
         upload DATETIME NOT NULL,
         update DATETIME,
         options VARCHAR(100),
         FOREIGN KEY(login) REFERENCES my_user(login)
    )
    """)

    ###### Get last version of browsers

    add_browser_sql = """ INSERT INTO browser(name, version)
                          VALUES(%(name)s, %(version)s)"""

    ### Firefox
    req = requests.get(ADDR_FIREFOX)

    # Parsing the HTML
    page = BfS(req.content, 'html.parser')

    # work on release part
    release_part = page.find('ol', class_='c-release-list')

    # take first link
    link = release_part.find('a')

    version = int(link.text.split('.')[0]) - 1

    cursor.execute(add_browser_sql, {'name':"Firefox", 'version':version})

    ### Chrome
    req = requests.get(ADDR_CHROME)

    # Parsing the HTML
    page = BfS(req.content, 'html.parser')

    # work on release part
    release_part = page.find_all('div', class_='post')

    for post in release_part:
        if 'Stable' in post.find('a').text:
            # Extract complete version
            version = re.findall('[0-9]*\.[0-9]*\.[0-9]*\.[0-9]*',
                                 post.text)[0]
            # main previous version
            version = int(version.split('.')[0]) - 1
            break

    cursor.execute(add_browser_sql, {'name':"Chrome", 'version':version})

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

    cursor.execute(add_browser_sql, {'name':"Edge", 'version':version})

    ### Safari
    op_fire = Options()
    op_fire.add_argument('--headless')
    driver = webdriver.Firefox(options=op_fire)
    driver.get(ADDR_SAFARI)
    version = WebDriverWait(driver, timeout=3).\
              until(lambda d: d.find_element(By.CLASS_NAME,"highlight"))
    version = version.text
    driver.quit()
    version = version.split()[1]
    version = int(version) - 1

    cursor.execute(add_browser_sql, {'name':"Safari", 'version':version})


def check_init(function):
    """
    Decorator check if database initiate else it initiate it

    Parameters
    ----------
    function : TYPE
        DESCRIPTION.

    Returns
    -------
    function

    """
    bool_base = False
    # Connect to data base
    cursor = connect_dbb()

    ### Check if database initiated
    # Query to check if table created
    exist_sql = """ SELECT EXISTS (SELECT FROM pg_tables
                                   WHERE tablename = 'inputs') """

    cursor.execute(exist_sql)

    if cursor.fetchone()[0]:
        # Check table browser is complet
        browser_sql = """SELECT version FROM browser WHERE name = 'Safari' """

        cursor.execute(browser_sql)

        if not cursor.fetchone is None and int(cursor.fetchone()[0]) > 10:
            bool_base = True

    # initialize database
    if bool_base is False :
        init_base()
