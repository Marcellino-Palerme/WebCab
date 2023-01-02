#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Nov  3 15:01:29 2022

@author: mpalerme
"""

import gettext as gt
import os
import re
import streamlit as st

# get path of directory translate
path_trans = os.path.join(os.path.dirname(__file__), 'msg')

# List of supported language
dic_lang = {'fr':{'name' : 'Français'},
            'en':{'name' : 'English'}}

for lang in dic_lang:

    dic_lang[lang]['trans'] = gt.translation('msg',
                                             localedir=path_trans,
                                             languages=[lang])

    dic_lang[lang]['trans'].install()

_ = dic_lang['fr']['trans'].gettext

save = 'fr'

def change():
    global _, save

    if 'lang' in st.session_state:
        save = st.session_state.lang
        _ = dic_lang[save]['trans'].gettext


def complet(code):

    return dic_lang[code]['name']

def select_language():
    """
    decorator add list to select the language

    Returns
    -------
    None.

    """

    index = list(dic_lang).index(save);

    # Add in sidebar language selector
    st.sidebar.selectbox('🌐', dic_lang, index=index, format_func=complet,
                         key='lang', on_change=change)

def link(txt):
    """
    create link in page

    Parameters
    ----------
    txt : str
        text.

    Returns
    -------
    None.

    """
    # Get text translated
    txt_trans = _(txt)

    # Create link
    # thx https://stackoverflow.com/a/8801066
    txt_link = re.sub('[^a-zA-Z0-9]', '-', txt_trans.lower())

    # Delete double -
    temp = txt_link.split('-')
    txt_link = '-'.join([x for x in temp if len(x)>0])

    return '[%s](#%s)' % (txt_trans, txt_link)
