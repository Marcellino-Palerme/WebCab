#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Sep 28 09:39:45 2022

@author: Marcellino Palerme

page to download processing images
"""
import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import streamlit as st
from authentification import login
from translate import _
from datetime import timedelta


#hashed_passwords = star.Hasher(['123', '456']).generate()
#st.write(hashed_passwords)
# Define title of page and menu
st.set_page_config(
    page_title=_("ddl pages streamlit"),
    page_icon="random",
    layout="wide",
    initial_sidebar_state="auto",
    menu_items={
        'Get Help': 'https://lesjoiesducode.fr/quand-on-na-pas-fourni-de-doc-aux-utilisateurs',
        'Report a bug': "https://forgemia.inra.fr/demecologie/web-cab/-/issues",
        'About': "first streamlit app"
    }
)

@login
def page():
    """
    compose page

    Returns
    -------
    None.

    """
    ### Get all processing of user
    # Define query
    user_proc_sql = """ SELECT uuid, state, upload, update FROM inputs
                        WHERE login=%(login)s;
                    """
    # Query database
    st.session_state.cursor.execute(user_proc_sql,
                                    {'login':st.session_state.login})

    path_temp = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    path_temp = os.path.join(path_temp,'temp')

    for uuid in st.session_state.cursor.fetchall():

        if 0<uuid[1]<100:
            with st.expander('🔬 ' + uuid[0] + _(' upload: ') +
                             uuid[2].strftime('%a %d %b %Y, %H:%M'),
                             expanded=False):
                st.progress(int(uuid[1]))
        elif uuid[1] == 0:
            with st.expander('⏳ ' + uuid[0] + _(' upload: ') +
                             uuid[2].strftime('%a %d %b %Y, %H:%M'),
                             expanded=False):
                st.text(_('Waiting'))
                st.markdown(':x:')
        elif uuid[1] == 100:
            with st.expander('🏁 ' + uuid[0] + _(' upload: ') +
                             uuid[2].strftime('%a %d %b %Y, %H:%M'),
                             expanded=False):
                st.text(_('Expiring: ') +
                        (uuid[3] +
                         timedelta(days=2)).strftime('%a %d %b %Y, %H:%M'))
                with open(os.path.join(path_temp, uuid[0] + '.zip'),
                          "rb") as zp_f:
                    st.download_button(_('download'), zp_f,
                                       uuid[0] + '.zip', 'application/zip')

if callable(page) :
    page()
