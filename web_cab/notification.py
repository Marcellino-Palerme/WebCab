#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Feb 24 09:27:28 2023

@author: mpalerme

Show notifications on web site
"""

import streamlit as st
import os
import sys
sys.path.append(os.path.dirname(__file__))
import connect as ct

def notif(*args, **kwargs):
    """


    Parameters
    ----------
    *args : TYPE
        DESCRIPTION.
    **kwargs : TYPE
        DESCRIPTION.

    Returns
    -------
    None.

    """
    _ = kwargs['trans']

    ### Get the futur update or upgrade
    # Define query
    updg_sql = """ SELECT * FROM wc_up
                   ORDER BY soon DESC;"""
    # Connect to database
    cursor = ct.connect_dbb()
    # Query database
    cursor.execute(updg_sql)

    updg = cursor.fetchone()

    # Show futur update
    if not updg is None:
        st.sidebar.markdown(_('Txt_futur_update_from_ht') + ' ' + str(updg[0])
                            + ' ' +_('Txt_futur_update_to_ht') + ' ' +
                            str(updg[1]), True)


    def inner(function):
        return function

    return inner
