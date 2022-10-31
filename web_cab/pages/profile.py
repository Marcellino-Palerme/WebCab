#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Oct 28 10:02:15 2022

@author: mpalerme

This page to see and manage the user profile
"""
import gettext as gt
import re
import streamlit as st
from web_cab.authentification import show
from streamlit_authenticator.exceptions import CredentialsError, ResetError

gt.bindtextdomain('web_cab', '/path/to/my/language/directory')
gt.textdomain('web_cab')
_ = gt.gettext



def valid_name(col):
    """
    Check if format of user name is correct

    Parameters
    ----------
    col : st.columns
        Column where write error message.

    Returns
    -------
    None.

    """
    # Thx https://www.autoregex.xyz/
    regex = '^[a-zA-Z0-9_-]{3,15}$'
    if re.match(regex, st.session_state.new_name) is None:
        col.markdown('<span style="color: red;" class="enclosing"><i>' +
                     _('msg_name_format_wrong') + '</i></span>', True)

        # Disable update name (part of global update)
        st.session_state.update_name = False
    else:
        # Enable update pwd (part of global update)
        st.session_state.update_name = True

def valid_email(col):
    """
    Check if format of email name is correct

    Parameters
    ----------
    col : st.columns
        Column where write error message.

    Returns
    -------
    None.
    """
    authr = st.session_state.authr
    # Thx https://www.autoregex.xyz/
    regex = r'[a-zA-Z0-9_.]+@[a-zA-Z0-9]+\.[a-zA-Z]{2,4}'
    if re.match(regex, st.session_state.new_name) is None:
        col.markdown('<span style="color: red;" class="enclosing"><i>' +
                      _('msg_email_format_wrong') + '</i></span>', True)

        # Disable update email (part of global update)
        st.session_state.update_email = False
    elif st.session_state.new_email == authr.get_email(\
                                                    st.session_state.username):
        # Disable update email (part of global update)
        st.session_state.update_email = False
    else:
        # Enable update email (part of global update)
        st.session_state.update_email = True

def update_label():
    """
    Update in database name and email of user

    Returns
    -------
    None.

    """
    authr = st.session_state.authr

    if st.session_state.update_name :
        # define query to update name user
        up_name_sql = '''UPDATE my_user
                         SET name=''' + st.session_state.new_name +\
                      '''WHERE email=''' +\
                         authr.get_email(st.session_state.username) + ';'

        # Update name user on database
        st.session_state.cursor.execute(up_name_sql)

        # Update name user on web site
        authr.update_name(st.session_state.username, st.session_state.new_name)

        st.session_state.update_name = False

    if st.session_state.update_email :
        # define query to update email user
        up_email_sql = '''UPDATE my_user
                         SET email=''' + st.session_state.new_email +\
                       '''WHERE email=''' +\
                          authr.get_email(st.session_state.username) + ';'

        # Update email user on database
        st.session_state.cursor.execute(up_email_sql)

        # Update email user on web site
        authr.update_email(st.session_state.username,
                           st.session_state.new_email)

        st.session_state.update_email = False

    st.success(_('msg_update_labels'))

def cancel_label():
    """
    Cancel modification of row

    Returns
    -------
    None.

    """
    authr = st.session_state.authr
    st.session_state.new_email = authr.get_email(st.session_state.username)
    st.session_state.new_name = st.session_state.name
    # Disable update name
    st.session_state.update_name = False
    # Disable update email
    st.session_state.update_email = False

@show
def page():
    """
    web page of profile

    Returns
    -------
    None.

    """

    # Enable update pwd
    st.session_state['update_pwd'] = True
    # Disable update name
    st.session_state['update_name'] = False
    # Disable update email
    st.session_state['update_email'] = False

    st.title(_('title_profile_page'))

    # use colunms to have name label, label, error message on same line
    a_col = st.columns(2)

    # Name label column
    with a_col[0] :
        st.text(_('row_login') + ': ' + st.session_state.username)
        st.text_input(_('row_name') + ':', st.session_state.name,
                      help=_('row_name_help'),
                      key='new_name', on_change=valid_name, args=(a_col[1],))
        st.text_input(_('row_email') + ':','tot',
                      #st.session_state.authr.credentials.\
                      #    get_email(st.session_state.username),
                      help=_('row_email_help'), key='new_email',
                      on_change=valid_email, args=(a_col[1],))

        st.button(_("bt_profile_update"), help=_("bt_profile_update_help"),
                  on_click=update_label)

        st.button(_('bt_profile_cancel'), help=_('bt_profile_cancel_help'),
                  on_click=cancel_label)


    st.button(_('bt_reset_pwd'), key='reset_pwd')
    if st.session_state.reset_pwd:

        try:
            if st.session_state.authr.reset_password(st.session_state.username,
                                                     _('title_reset_pwd')):
                st.success(_('msg_pwd_update'))

                # hide reset pwd form
                st.session_state.reset_pwd = False
        except (ResetError, CredentialsError) as e_up_pwd:
            st.error(_(e_up_pwd))


if callable(page) :
    page()
