#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Feb 28 11:53:16 2023

@author: mpalerme
"""

import sys
import os
import json

dir_conf = sys.argv[1]

# Check if there is a conf file
if len(sys.argv) == 3 and os.path.exists(os.path.join(dir_conf, 'conf.json')):
    print('y')
elif len(sys.argv) == 3 and not (os.path.exists(os.path.join(dir_conf, 'conf.json'))):
    print('n')
else:
    with open(os.path.join(dir_conf, 'conf.json'), 'w',
              encoding='utf-8') as jconf:
        d_conf = json.load(jconf)
    print(d_conf['db']['password'])
