#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Nov  3 15:01:29 2022

@author: mpalerme
"""

import gettext as gt
import os
import re

# get path of directory translate
path_trans = os.path.join(os.path.dirname(__file__), 'msg')
lang = gt.translation('msg',
                      localedir=path_trans,
                      languages=['fr'])
lang.install()
_ = lang.gettext

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

    return '[%s](#%s)' % (txt_trans, txt_link)
