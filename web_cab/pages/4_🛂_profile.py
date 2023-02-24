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
import datetime



# Define title of page and menu
st.set_page_config(
    page_title=_('Title_profile'),
    page_icon="🛂",
    layout="wide",
    initial_sidebar_state="auto"
)

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


def delete_upgrade():
    """
    Delete futur upgrade

    Returns
    -------
    None.

    """
    # Define query
    del_upgrade_sql = """ DELETE FROM wc_up
                          WHERE date_grade=false;"""
    # Query database
    st.session_state.cursor.execute(del_upgrade_sql)

def add_upgrade(where_display, date_start, date_end, time_start, time_end):
    """
    add futur upgrade

    Parameters
    ----------
    where_display : streamlit container
        Part where display tab.
    date_start : TYPE
        DESCRIPTION.
    date_end : TYPE
        DESCRIPTION.
    time_start : TYPE
        DESCRIPTION.
    time_end : TYPE
        DESCRIPTION.

    Returns
    -------
    None.

    """
    start = datetime.datetime.combine(date_start, time_start)
    end = datetime.datetime.combine(date_end, time_end)
    if datetime.datetime.today() > start:
        where_display.error(_("msg_error_upgrade_date_no_futur"))
    elif start > end:
        where_display.error(_("msg_error_upgrade_start_end"))
    else:
        ### Add the futur upgrade
        # Define query
        upgrade_sql = """ INSERT INTO wc_up (soon, completion, date_grade)
                          VALUES (%(start)s, %(end)s, true);"""
        # Query database
        st.session_state.cursor.execute(upgrade_sql,{'start':start.isoformat(),
                                                     'end':end.isoformat()})



def update_tab(where_display):
    """
    Define tab administrateur to view futur update and manage upgrade

    Parameters
    ----------
    where_display : streamlit container
        Part where display tab.

    Returns
    -------
    None.

    """
    ### Get the futur update
    # Define query
    updg_sql = """ SELECT * FROM wc_up
                 WHERE date_grade=false
                 ORDER BY soon DESC;"""
    # Query database
    st.session_state.cursor.execute(updg_sql)

    updg = st.session_state.cursor.fetchone()

    # Show futur update
    if not updg is None:
        where_display.markdown(_('Txt_futur_update_ht') + str(updg[0]), True)

    ### Get the futur upgrade
    # Define query
    up_sql = """ SELECT * FROM wc_up
                 WHERE date_grade=true
                 ORDER BY soon DESC;"""
    # Query database
    st.session_state.cursor.execute(up_sql)

    updg = st.session_state.cursor.fetchone()

    # Show futur update
    if not updg is None:
        a_col = where_display.columns((5,1))
        a_col[0].markdown(_('Txt_futur_upgrade_ht') + str(updg[0]), True)
        a_col[0].button('❌', help=_("bt_upgrade_delete_help"),
                        on_click=delete_upgrade)
    else:
        where_display.markdown(_('Title_define_futur_upgrade_ht'), True)
        a_col = where_display.columns((3,3,5))
        date_start = a_col[0].date_input(_('label_upgrade_date_start'))
        date_end = a_col[0].date_input(_('label_upgrade_date_end'))
        time_start = a_col[1].time_input(_('label_upgrade_time_start'))
        time_end = a_col[1].time_input(_('label_upgrade_time_end'))
        where_display.button(_('bt_upgrade_add'),
                             help=_('bt_upgrade_add_help'),
                             on_click=add_upgrade, args=(where_display,
                                                         date_start, date_end,
                                                         time_start, time_end))


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
                          _('tab_admin_delete'), _('tab_admin_update')])
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
        update_tab(l_tabs[3])


if callable(page) :
    page()
