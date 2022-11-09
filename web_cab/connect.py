#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Nov  9 14:29:24 2022

@author: mpalerme

Provide function to connect to database
"""
import json
import psycopg2 as pc2

def connect_dbb():
    """


    Returns
    -------
    None.

    """
    # Get configurations
    with open('./web_cab/conf/conf.json', 'r', encoding='utf-8') as f_conf:
        d_conf = json.load(f_conf)

    ### Get all user information
    # Connect to database
    conn = pc2.connect(**d_conf['db'])
    conn.autocommit = True

    return conn.cursor()
