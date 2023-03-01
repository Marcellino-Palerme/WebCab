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

sys.path.append(os.path.dirname(__file__))
from connect import connect_dbb

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
    ADDR_SAFARI = 'https://developer.apple.com/documentation/safari-release-notes'

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
    # This part fails because this web page is completly in javascript
    # When you update streamlit check an change if necessary value of version
    # of Safari
    """
    req = requests.get(ADDR_SAFARI)

    # Parsing the HTML
    page = BfS(req.content, 'html.parser')

    summary_part = page.find('div', class_='toc')

    release_part=summary_part.find_all('span')

    for release in release_part:
        if 'Safari' in release.text and not 'o' in release.text:
            version = int(release.text.split('Safari')[1])

    version = int(version) - 1
    """

    version = 16 - 1

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

    ### Create all tables

    # Table to manage browser version support
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS browser(
         name VARCHAR(20) PRIMARY KEY UNIQUE NOT NULL,
         version INTEGER
    )
    """)

    # Define status user type
    cursor.execute("""
                   DO $$
                   BEGIN
                      IF NOT EXISTS (SELECT 1 FROM pg_type
                                     WHERE typname = 'status_type') THEN
                         CREATE TYPE status_type AS
                         ENUM ('', 'super', 'temp', 'temp_super');
                     END IF;
                  END$$;""")

    # Table to manage user
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS my_user(
         login VARCHAR(20) PRIMARY KEY UNIQUE NOT NULL,
         email VARCHAR(50) UNIQUE NOT NULL,
         pwd VARCHAR(200),
         status status_type
    )
    """)

    # Table to manage asked process
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS inputs(
         uuid VARCHAR(40) PRIMARY KEY UNIQUE,
         login VARCHAR(20) NOT NULL,
         size INTEGER,
         state INTEGER,
         upload TIMESTAMP NOT NULL,
         update TIMESTAMP,
         options VARCHAR(100),
         download BOOL,
         FOREIGN KEY(login) REFERENCES my_user(login)
    )
    """)

    # Table to manage update (the field date_grade: false mean update,
    # true upgrade)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS wc_up(
        soon TIMESTAMP NOT NULL,
        completion TIMESTAMP NOT NULL,
        date_grade BOOL
    )
    """)

    ### Restore old base
    if os.path.exists(os.path.join(os.path.dirname(__file__),'conf',
                                   'save.json')):
        with open(os.path.join(os.path.dirname(__file__),'conf','save.json'),
              'r', encoding='utf-8') as jsave:
            d_base = json.load(jsave)

        for record in d_base['my_user']:
            user_sql ="""INSERT INTO my_user(login, email, pwd, status)
                       VALUES(%(login)s, %(email)s, %(pwd)s, %(status)s)"""
            # Query database
            cursor.execute(user_sql, record)

        for record in d_base['inputs']:
            user_sql ="""INSERT INTO inputs(uuid, login, size, state, upload,
                                            update, options, download)
                       VALUES(%(uuid)s, %(login)s, %(size)s, %(state)s,
                              %(upload)s, %(update)s, %(options)s,
                              %(download)s)"""
            # Query database
            cursor.execute(user_sql, record)

    else:
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

    cursor.close()

    return function
