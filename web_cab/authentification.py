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


gt.bindtextdomain('web_cab', '/path/to/my/language/directory')
gt.textdomain('web_cab')
_ = gt.gettext

class MyAuthen():
    """
    authentification
    """

    def __init__(self, cursor):
        self.cursor = cursor


    def _get_email(self, username):
        """
        Get email of user

        Parameters
        ----------
        username : str
            login of user.

        Returns
        -------
        email: str.

        """
        email_sql = "SELECT email FROM my_user WHERE login = %(username)s"
        self.cursor.execute(email_sql, {'username':username})
        email = self.cursor.fetchone()
        if email is None:
            return False

        return email[0]


    def _get_pwd(self, username):
        """
        Get pwd of user

        Parameters
        ----------
        username : str
            username of user.

        Returns
        -------
        password: str.

        """
        if self._valid_username(username):
            # Get  pwd
            pwd_sql = """SELECT pwd FROM my_user WHERE login = %(username)s"""

            self.cursor.execute(pwd_sql, {'username':username})
            return self.cursor.fetchone()[0]

        return ""

    def _valid_pwd(self, username, pwd):
        """


        Returns
        -------
        TYPE
            DESCRIPTION.

        """
        return bcrypt.checkpw(pwd.encode(),
                              self._get_pwd(username).encode())

    def login(self) -> tuple:
        """
        Creates a login widget.
        Parameters
        ----------
        form_name: str
            The rendered name of the login form.
        Returns
        -------
        str
            Name of the authenticated user.
        int
            The status of authentication, None: no credentials entered,
            True: correct credentials, False: incorrect credentials,
        str
            Username of the authenticated user.
        """
        st.session_state['miss'] = False
        if ('authentication_status' not in st.session_state or
            st.session_state.authentication_status is not True):
            st.session_state['authentication_status'] = False
            login_form = st.form('Login')

            login_form.subheader(_('title_form_login'))
            login_form.text_input(_('form_login_username'), key='username')
            pwd = login_form.text_input(_('form_login_pwd'), type='password')

            if login_form.form_submit_button('Login'):
                ### Verify input not empty
                # Thx https://stackoverflow.com/a/5063991
                regex_no_empty = r'[^$^\ ]'
                if(re.match(regex_no_empty, st.session_state.username) is None or
                   re.match(regex_no_empty, pwd) is None):
                    st.session_state.miss = True
                else:
                    if self._valid_pwd(st.session_state.username, pwd):
                        st.session_state['authentication_status'] = True


    def _update_pwd(self, username, pwd):
        """


        Parameters
        ----------
        username : TYPE
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
                     WHERE login=%(username)s;"
        # Query database
        self.cursor.execute(up_pwd_sql,
                            {'hsh_pwd':hsh_pwd, 'username':username})


    def _gen_pwd(self, username):
        """


        Parameters
        ----------
        username : TYPE
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
        self._update_pwd(username, pwd)

        return pwd

    def _valid_username(self, username):
        """


        Parameters
        ----------
        username : TYPE
            DESCRIPTION.

        Returns
        -------
        None.

        """
        login_sql = "SELECT login FROM my_user WHERE login ~* %(start_login)s"
        start_login = '^' + username[0]
        self.cursor.execute(login_sql, {'start_login':start_login})
        l_login_pwd = self.cursor.fetchall()
        # Check if username exist
        for user in l_login_pwd:
            if user[0] == username:
                # return login
                return True

        return False

    def forgot_pwd(self, form_name: str) -> tuple:
        """
        Creates a forgot password widget.
        Parameters
        ----------
        form_name: str
            The rendered name of the forgot password form.

        Returns
        -------
        str
            Username associated with forgotten password.
        str
            Email associated with forgotten password.
        str
            New plain text password that should be transferred to user securely.
        """

        forgot_password_form = st.form('Forgot password')


        forgot_password_form.subheader(form_name)
        forgot_password_form.text_input(_('Username'),
                                        key='v_forgot_pwd').lower()

        st.session_state['state_forgot_pwd'] = 3
        v_return = (None, None, None)
        def inside():
            username = st.session_state.v_forgot_pwd
            # Thx https://stackoverflow.com/a/5063991
            regex_no_empty = r'[^$^\ ]'
            if not re.match(regex_no_empty, username) is None :
                if self._valid_username(username):
                    st.session_state['state_forgot_pwd'] = 0
                    ### Modify user password
                    pwd = self._gen_pwd(username)

                    # Send temporary paswword by email
                    email = self._get_email(username)
                    send_email(dst=email, sub=_('msg_email_sub_pwd'),
                               msg=_('msg_email_header_pwd') + pwd +
                                   _('msg_email_end'))

                else:
                    st.session_state['state_forgot_pwd'] = 1
            else:
                st.session_state['state_forgot_pwd'] = 2

            del st.session_state.v_forgot_pwd


        forgot_password_form.form_submit_button(_('Submit'), on_click=inside)

        return v_return



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
    if 'authentication_status' in st.session_state :
        if st.session_state.authentication_status:
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
    forgot_status, email = st.session_state.authr.forgot_username(
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
            st.session_state.authr.forgot_pwd(_('title_forgot_pwd'))

    with a_col[1]:
        st.button(_('bt_forgot_login'), help=_('bt_forgot_login_help'), on_click=
                  forgot_login)

def init_login():
    """


    Returns
    -------
    None.

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
    init_login()
    authr = st.session_state['authr']

    # Show widget login
    authr.login()

    if st.session_state.authentication_status is not True:
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
    if st.session_state.authentication_status is True :
        # add acces profile and logout on sidebar
        #authr.logout(_('bt_logout'), 'sidebar')
        v_return = function
    elif st.session_state.miss is True :
        st.info(_('msg_login_miss'))
    elif st.session_state.authentication_status is False :
        st.error(_('msg_login_fail'))
    return v_return
