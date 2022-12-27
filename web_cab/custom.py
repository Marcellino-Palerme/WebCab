#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Dec 27 13:15:53 2022

@author: mpalerme

Custom streamlit app
"""

import streamlit as st


def hide_hamburger(function):
    """
    hide the hamburger menu

    Returns
    -------
    function.

    """
    hide_menu_style = """
                        <style>
                            #MainMenu {visibility: hidden;}
                        </style>
                      """
    st.markdown(hide_menu_style, unsafe_allow_html=True)

    return function
