#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Oct 27 11:22:18 2022

@author: mpalerme
"""
import json
import re
import gettext as gt
import psycopg2 as pc2
import streamlit as st
from web_cab.email import send_email
import bcrypt
import numpy as np
from streamlit_javascript import st_javascript as stj


gt.bindtextdomain('web_cab', '/path/to/my/language/directory')
gt.textdomain('web_cab')
_ = gt.gettext

class MyAuthen():
    """
    authentification
    """

    def __init__(self, cursor):
        self.cursor = cursor


    def _get_email(self, i_login):
        """
        Get email of user

        Parameters
        ----------
        login : str
            login of user.

        Returns
        -------
        email: str.

        """
        email_sql = "SELECT email FROM my_user WHERE login = %(login)s"
        self.cursor.execute(email_sql, {'login':i_login})
        email = self.cursor.fetchone()
        if email is None:
            return False

        return email[0]


    def _get_pwd(self, i_login):
        """
        Get pwd of user

        Parameters
        ----------
        login : str
            login of user.

        Returns
        -------
        password: str.

        """
        if self._valid_login(i_login):
            # Get  pwd
            pwd_sql = """SELECT pwd FROM my_user WHERE login = %(login)s"""

            self.cursor.execute(pwd_sql, {'login':i_login})
            return self.cursor.fetchone()[0]

        return ""

    def _valid_pwd(self, i_login, pwd):
        """


        Returns
        -------
        TYPE
            DESCRIPTION.

        """
        return bcrypt.checkpw(pwd.encode(),
                              self._get_pwd(i_login).encode())

    def login(self):
        """
        Creates a login widget.

        """
        st.session_state['miss'] = False
        if ('auth_status' not in st.session_state or
            st.session_state.auth_status is not True):
            st.session_state['auth_status'] = None
            login_form = st.form('Login')

            login_form.subheader(_('title_form_login'))
            login_form.text_input(_('form_login_login'), key='login')
            pwd = login_form.text_input(_('form_login_pwd'), type='password')

            if login_form.form_submit_button(_('bt_login_submit')):
                ### Verify input not empty
                # Thx https://stackoverflow.com/a/5063991
                regex_no_empty = r'[^$^\ ]'
                if(re.match(regex_no_empty, st.session_state.login) is None or
                   re.match(regex_no_empty, pwd) is None):
                    st.session_state.miss = True
                else:
                    if self._valid_pwd(st.session_state.login, pwd):
                        st.session_state['auth_status'] = True
                    else:
                        st.session_state['auth_status'] = False


    def _update_pwd(self, i_login, pwd):
        """


        Parameters
        ----------
        login : TYPE
            DESCRIPTION.
        pwd : TYPE
            DESCRIPTION.

        Returns
        -------
        None.

        """
        hsh_pwd = bcrypt.hashpw(pwd.encode(), bcrypt.gensalt()).decode()

        # query for modification
        up_pwd_sql ="UPDATE my_user SET status='temp', pwd=%(hsh_pwd)s \
                     WHERE login=%(login)s;"
        # Query database
        self.cursor.execute(up_pwd_sql,
                            {'hsh_pwd':hsh_pwd, 'login':i_login})


    def _gen_pwd(self, i_login):
        """


        Parameters
        ----------
        login : TYPE
            DESCRIPTION.

        Returns
        -------
        None.

        """
        # Define size of password
        size_pwd = np.random.randint(12, 31)
        type_pwd = np.dtype((str, size_pwd))

        # Generate a password (32 in Ascii is Space and 126 is ~)
        pwd = np.random.randint(low=32, high=126, size=size_pwd,
                                dtype="int32").view(type_pwd)[0]

        # save Hashed password
        self._update_pwd(i_login, pwd)

        return pwd

    def _valid_login(self, i_login):
        """


        Parameters
        ----------
        login : TYPE
            DESCRIPTION.

        Returns
        -------
        None.

        """
        login_sql = "SELECT login FROM my_user WHERE login ~* %(start_login)s"
        start_login = '^' + i_login[0]
        self.cursor.execute(login_sql, {'start_login':start_login})
        l_login_pwd = self.cursor.fetchall()
        # Check if login exist
        for user in l_login_pwd:
            if user[0] == i_login:
                # return login
                return True

        return False

    def forgot_pwd(self):
        """
        Creates a forgot password widget.

        """

        forgot_password_form = st.form('Forgot password')


        forgot_password_form.subheader(_('title_forgot_pwd'))
        forgot_password_form.text_input(_('forgot_pwd_login'),
                                        key='v_forgot_pwd')

        st.session_state['state_forgot_pwd'] = 3

        def inside():
            v_login = st.session_state.v_forgot_pwd
            # Thx https://stackoverflow.com/a/5063991
            regex_no_empty = r'[^$^\ ]'
            if not re.match(regex_no_empty, v_login) is None :
                if self._valid_login(v_login):
                    st.session_state['state_forgot_pwd'] = 0
                    ### Modify user password
                    pwd = self._gen_pwd(v_login)

                    # Send temporary paswword by email
                    email = self._get_email(v_login)
                    send_email(dst=email, sub=_('msg_email_sub_pwd'),
                               msg=_('msg_email_header_pwd') + pwd +
                                   _('msg_email_end'))

                else:
                    st.session_state['state_forgot_pwd'] = 1
            else:
                st.session_state['state_forgot_pwd'] = 2

            del st.session_state.v_forgot_pwd


        forgot_password_form.form_submit_button(_('bt_forgot_pwd_submit'),
                                                on_click=inside)


    def logout(self):
        """
        provide a button on sidebar to logout

        Returns
        -------
        None.

        """
        def inside():
            del st.session_state.auth_status
            stj('location.href = location.hostname;')

        st.sidebar.button(_('bt_logout'), help=_('bt_logout_help'),
                          on_click=inside)




def vide():
    """
    empty function

    Returns
    -------
    None.

    """


def show(function):
    """
    Decorator
    Show page or not, depend of login

    Parameters
    ----------
    function : TYPE
        DESCRIPTION.

    Returns
    -------
    None.

    """
    if 'auth_status' in st.session_state :
        if st.session_state.auth_status:
            return function

    return vide

def forgot_login():
    """
    send login of user

    Returns
    -------
    None.

    """
    # Verify if email exist
    forgot_status, email = st.session_state.authr.forgot_login(
                           _('title_forgot_login'))

    if forgot_status :
        # Get login of user
        get_login_sql = '''SELECT login
                           FROM my_user
                           WHERE email=''' + email + ';'
        l_login = st.session_state.cursor.execute(get_login_sql)
        l_login = l_login.fetchone()

        # Send login user
        send_email(dst=email, sub=_('msg_email_sub_login'),
                   msg=_('msg_email_header_login') + l_login[0] + \
                         _('msg_email_end'))


    elif forgot_status is False :
        pass

    elif forgot_status is None :
        pass

    st.stop()

def not_logged(function):
    """
    Decorator
    Run or not function if user logged

    Parameters
    ----------
    function : TYPE
        DESCRIPTION.

    Returns
    -------
    function

    """
    if 'authentification_status' in st.session_state:
        if st.session_state.authentification_status:
            return vide
    return function

@not_logged
def forgot():
    """
    Add button if you forget a part to sign in

    Returns
    -------
    None.

    """
    a_col = st.columns(5)
    with a_col[0]:
        if st.button(_('bt_forgot_pwd'), help=_('bt_forgot_pwd_help')):
            st.session_state.authr.forgot_pwd()

    with a_col[1]:
        st.button(_('bt_forgot_login'), help=_('bt_forgot_login_help'), on_click=
                  forgot_login)


def login(function):
    """
    Decorator to manage the sign in

    Parameters
    ----------
    function : TYPE
        DESCRIPTION.

    Returns
    -------
    function

    """
    # Get configurations
    with open('./web_cab/conf/conf.json', 'r', encoding='utf-8') as f_conf:
        d_conf = json.load(f_conf)

    ### Get all user information
    # Connect to database
    conn = pc2.connect(**d_conf['db'])
    conn.autocommit = True
    cursor = conn.cursor()
    st.session_state['cursor'] = cursor

    ### Manage sign in
    # initiate login widget
    authr = MyAuthen(cursor)

    # Save obj in session
    st.session_state['authr'] = authr

    # Show widget login
    authr.login()

    if st.session_state.auth_status is not True:
        # Add buttons for forgot password or login
        forgot()

    if 'state_forgot_pwd' in st.session_state:
        if st.session_state.state_forgot_pwd == 1 :
            st.error(_('msg_forgot_pwd_fail'))
        elif st.session_state.state_forgot_pwd == 2:
            st.info(_('msg_forgot_pwd_miss'))
        elif st.session_state.state_forgot_pwd == 0:
            st.info(_('msg_forgot_pwd_ok'))
        del st.session_state.state_forgot_pwd

    v_return = vide
    if st.session_state.auth_status is True :
        # add acces profile and logout on sidebar
        authr.logout()
        v_return = function
    elif st.session_state.miss is True :
        st.info(_('msg_login_miss'))
    elif st.session_state.auth_status is False :
        st.error(_('msg_login_fail'))
    return v_return
