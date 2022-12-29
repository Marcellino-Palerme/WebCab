#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Oct 28 10:02:15 2022

@author: mpalerme

This page to see and manage the user profile
"""
import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from translate import _, select_language
import streamlit as st
from authentification import login
from browser import browser_ok
from init_bdd import check_init
from custom import hide_hamburger

def cancel_label():
    """
    Cancel modification of row

    Returns
    -------
    None.

    """
    authr = st.session_state.authr
    if 'new_email' in  st.session_state :
        st.session_state.new_email = authr.get_email(st.session_state.login)

select_language()

@login(trans=_)
@browser_ok
@check_init
@hide_hamburger
def page():
    """
    web page of profile

    Returns
    -------
    None.

    """

    st.title(_('title_profile_page'))

    l_tabs=[None]

    if st.session_state.super is True:
        l_tabs = st.tabs([_('tab_user'), _('tab_admin_create'),
                          _('tab_admin_delete')])
    else:
        l_tabs[0] = st


    ### Tab to show and modify own profile

    # use colunms to have name label, label, error message on same line
    a_col = [None, None]
    a_col[0] = l_tabs[0].columns(2)

    # Name label column
    with a_col[0][0] :
        l_tabs[0].text(_('row_login') + ': ' + st.session_state.login)

        l_tabs[0].text_input(_('row_email') + ':',
                      st.session_state.authr.get_email(st.session_state.login),
                      help=_('row_email_help'), key='new_email')

    a_col[1] = l_tabs[0].columns(7)
    with a_col[1][0] :
        l_tabs[0].button(_("bt_profile_update"), help=_("bt_profile_update_help"),
                  on_click=st.session_state.authr.update_email,
                  args=(st.session_state.login, st.session_state.new_email,
                        a_col[0][1]))

    with a_col[1][2] :
        l_tabs[0].button(_('bt_profile_cancel'), help=_('bt_profile_cancel_help'),
                  on_click=cancel_label)


    l_tabs[0].button(_('bt_change_pwd'), help=_('bt_change_pwd_help'),
                     on_click= st.session_state.authr.change_pwd,
                     args=(l_tabs[0],))

    ### Tab to show and modify other profiles administrateur part
    if st.session_state.super is True:
        st.session_state.authr.create_user(l_tabs[1])
        st.session_state.authr.delete_user(l_tabs[2])

if callable(page) :
    page()
