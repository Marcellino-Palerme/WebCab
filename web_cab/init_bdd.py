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
import json
import shutil
import subprocess

sys.path.append(os.path.dirname(__file__))
from connect import connect_dbb

def update_geckodriver():
    """
    Install or update geckodriver for selenium

    Returns
    -------
    None.

    """
    ADDR_GECKODRIVER = "https://github.com/mozilla/geckodriver/releases/latest"
    temp_ddl='https://github.com/mozilla/geckodriver/releases/download/v<ver>/geckodriver-v<ver>-linux64.tar.gz'

    ### Info on last release of geckodriver
    req = requests.get(ADDR_GECKODRIVER)

    # Parsing the HTML
    page = BfS(req.content, 'html.parser')

    # work on release part
    release_part = page.find('nav', class_='mb-5')

    # take second link
    link = release_part.find_all('a')[1]

    # Take version without 'v' and '\n' caracter
    last_version = link.text.split(sep='v')[1][:-1]

    # Check if geckodriver installed
    path = shutil.which('geckodriver')

    in_version = '0.0.0'
    if not path is None:
        in_version = subprocess.run(["geckodriver", "-V"], capture_output=True)
        in_version = in_version.stdout.split()[1].decode()
    else:
        # Define where put software
        path = '/usr/bin'

    # Check in version is up to date
    if last_version > in_version:
        # Create link to download
        link_ddl = temp_ddl.replace('<ver>', last_version)
        # Get software
        subprocess.run(['wget', link_ddl])
        # Save it
        subprocess.run(['tar', 'xf', '*.tar.gz'])
        subprocess.run(['mv', 'geckodriver', path])


def update_browser_version(cursor):
    """
    Add or update version of supported streamlit browser

    Parameters
    ----------
    cursor : TYPE
        cursor to database.

    Returns
    -------
    None.

    """

    # Define address to get last broswer version
    ADDR_FIREFOX = "https://www.mozilla.org/en-US/firefox/releases/"
    ADDR_CHROME = "https://chromereleases.googleblog.com/search/label/Desktop%20Update"
    ADDR_EDGE = "https://learn.microsoft.com/en-us/deployedge/microsoft-edge-release-schedule"
    ADDR_SAFARI = 'https://en.wikipedia.org/wiki/Safari_(web_browser)'

    ### Firefox
    add_browser_sql = """ INSERT INTO browser (name, version)
                          VALUES(%(name)s, %(version)s)
                          ON CONFLICT (name) DO UPDATE SET version=%(version)s
                          """

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
    req = requests.get(ADDR_SAFARI)

    # Parsing the HTML
    page = BfS(req.content, 'html.parser')

    summary_part = page.find('div', class_='toc')

    release_part=summary_part.find_all('span')

    for release in release_part:
        if 'Safari' in release.text and not 'o' in release.text:
            version = int(release.text.split('Safari')[1])

    version = int(version) - 1

    cursor.execute(add_browser_sql, {'name':"Safari", 'version':version})


def init_base(cursor):
    """
    Initialise the database

    Parameters
    ----------
    cursor : TYPE
        cursor to database.

    Returns
    -------
    None.

    """


    # Prepare software for selenium
    update_geckodriver()

    # Create all tables
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS browser(
         name VARCHAR(20) PRIMARY KEY UNIQUE NOT NULL,
         version INTEGER
    )
    """)

    cursor.execute("""
                   DO $$
                   BEGIN
                      IF NOT EXISTS (SELECT 1 FROM pg_type
                                     WHERE typname = 'status_type') THEN
                         CREATE TYPE status_type AS
                         ENUM ('', 'super', 'temp', 'temp_super');
                     END IF;
                  END$$;""")

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
         size INTEGER,
         state INTEGER,
         upload TIMESTAMP NOT NULL,
         update TIMESTAMP,
         options VARCHAR(100),
         FOREIGN KEY(login) REFERENCES my_user(login)
    )
    """)

    #### Add admin user
    # Get configuration
    # Get configurations
    with open(os.path.join(os.path.dirname(__file__),'conf','conf.json'),
              'r', encoding='utf-8') as f_conf:
        d_conf = json.load(f_conf)

    # Query to add admin user
    admin_sql = """INSERT INTO my_user(login, email, status)
                   VALUES(%(login)s, %(email)s, %(status)s)"""

    # Query database
    cursor.execute(admin_sql, {'login':d_conf['login'],
                               'email':d_conf['email'],
                               'status':'super'})

    ###### Get last version of browsers


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
        browser_sql = """SELECT EXISTS(SELECT FROM browser
                                       WHERE name='Safari')"""

        cursor.execute(browser_sql)

        bool_base = bool(cursor.fetchone()[0])

    # initialize database
    if bool_base is False :
        init_base(cursor)
        update_browser_version(cursor)
