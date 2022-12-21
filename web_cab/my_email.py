#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Oct 27 15:49:54 2022

@author: mpalerme
"""
import os


def send_email(dst, sub, msg):
    with open(os.path.join(os.path.dirname(__file__), 'pwd.txt'), 'w') as fp:
        print(msg, file=fp)
