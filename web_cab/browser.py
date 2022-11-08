#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Nov  8 15:06:19 2022

@author: mpalerme
"""
import streamlit as st
from streamlit_javascript import st_javascript
import sqlite3
import os

def empty_function():
    """


    Returns
    -------
    None.

    """


def browser_ok(function):
    # Verify broswer is compatible
    # Get info on browser client
    info_brow = str(st_javascript("""navigator.userAgent"""))
    conn = sqlite3.connect(os.path.join(os.getcwd(),'web_cab','ma_base.db'))
    cursor = conn.cursor()

    st.session_state['browser'] = False

    brow_comp = True
    if 'Edg' in info_brow:
        cursor.execute("""SELECT version FROM browser WHERE name='Edge'""")
        min_version = cursor.fetchone()[0]
        if int(info_brow.split('Edg/')[1].split('.')[0]) < min_version:
            brow_comp = False
    elif 'Firefox' in info_brow:
        cursor.execute("""SELECT version FROM browser WHERE name='Firefox'""")
        min_version = cursor.fetchone()[0]
        if int(info_brow.split('Firefox/')[1].split('.')[0]) < min_version:
            brow_comp = False
    elif 'Chrome' in info_brow:
        cursor.execute("""SELECT version FROM browser WHERE name='Chrome'""")
        min_version = cursor.fetchone()[0]
        if int(info_brow.split(sep='Chrome/')[1].split(sep='.')[0]) < min_version:
            brow_comp = False
    elif 'Safari' in info_brow:
        cursor.execute("""SELECT version FROM browser WHERE name='Safari'""")
        min_version = cursor.fetchone()[0]
        if int(info_brow.split('Safari/')[1].split('.')[0]) < min_version:
            brow_comp = False
    else:
        brow_comp = False

    if brow_comp:
        st.session_state['browser'] = True
        return function
    st.write('Update your Broswer (Firefox, Chrome, Edge, Safari)')
    return empty_function
