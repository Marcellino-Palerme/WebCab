#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Nov  3 15:01:29 2022

@author: mpalerme
"""

import gettext as gt
import os


# get path of directory translate
path_trans = os.path.join(os.path.dirname(__file__), 'msg')
lang = gt.translation('msg',
                      localedir=path_trans,
                      languages=['fr'])
lang.install()
_ = lang.gettext
