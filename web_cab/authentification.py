#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Oct 27 11:22:18 2022

@author: mpalerme
"""
import json
import re
from web_cab.translate import _
import psycopg2 as pc2
import streamlit as st
from web_cab.email import send_email
import bcrypt
import numpy as np
import csv
import os

def keyword_inside(sentence):
    """
    check if there are a keyword in sentence

    Parameters
    ----------
    sentence : str
        analysed sentence.

    Returns
    -------
    bool
        True: there is a keyword in sentence.

    """
    # get path of .csv with keywords of postgresql
    path_keyword = os.path.join(os.path.dirname(__file__), 'extras',
                                'keywords.csv')

    f_key = open(path_keyword, 'r')
    # get all keywords
    reader = csv.reader(f_key)

    for key in reader:
        # Check if a keyword is in sentence
        if key[0].upper() in sentence.upper():
            f_key.close()
            return True

    return False



def valid_email(i_login, email, col):
    """
    Check if format of email name is correct

    Parameters
    ----------
    col : st.columns
        Column where write error message.

    Returns
    -------
    bool.
    """
    authr = st.session_state.authr
    # Thx https://www.autoregex.xyz/
    regex = r'[a-zA-Z0-9_.]+@[a-zA-Z0-9]+\.[a-zA-Z]{2,4}'
    if re.match(regex, email) is None:
        col.markdown('<span style="color: red;" class="enclosing"><i>' +
                      _('msg_change_email_wrong') + '</i></span>', True)

        return False
    elif email == authr.get_email(i_login):
        col.markdown('<span style="color: blue;" class="enclosing"><i>' +
                      _('msg_change_email_same') + '</i></span>', True)

        return False
    return True


class MyAuthen():
    """
    authentification
    """

    def __init__(self, cursor):
        self.cursor = cursor


    def get_email(self, i_login):
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

        if not self._valid_login(i_login):
            return ''
        email_sql = "SELECT email FROM my_user WHERE login = %(login)s"
        self.cursor.execute(email_sql, {'login':i_login})
        email = self.cursor.fetchone()
        if email is None:
            return ''

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

    def _is_admin(self, i_login):
        """
        Indicate if user is a administrateur

        Parameters
        ----------
        i_login : str
            Login of user

        Returns
        -------
        Bool
            True : user is a administrateur

        """
        if(self._valid_login(i_login)):
            admin_sql = """SELECT (CASE WHEN status = 'super'  OR
                                             status = 'temp_super'
                                        THEN 1 ELSE 0 END) AS admin
                           FROM my_user WHERE login = %(login)s;"""
            self.cursor.execute(admin_sql, {'login': i_login})

            if self.cursor.fetchone()[0] == 1:
                return True

        return False

    def login(self):
        """
        Creates a login widget.

        """
        st.session_state['miss'] = False
        if ('auth_status' not in st.session_state or
            st.session_state.auth_status is not True):
            st.session_state['auth_status'] = None
            st.session_state['login'] = None
            st.session_state['super'] = False

            # Thx https://discuss.streamlit.io/t/delete-remove-from-app-screen
            #-streamlit-form-st-form-after-feeling/25041/2
            placeholder = st.empty()

            login_form = placeholder.form('Login')

            login_form.subheader(_('title_form_login'))
            login_form.text_input(_('form_login_login'), key='in_login')
            pwd = login_form.text_input(_('form_login_pwd'), type='password')

            if login_form.form_submit_button(_('bt_login_submit')):
                ### Verify input not empty
                # Thx https://stackoverflow.com/a/5063991
                regex_no_empty = r'[^$^\ ]'
                if(re.match(regex_no_empty, st.session_state.in_login) is None
                   or
                   re.match(regex_no_empty, pwd) is None):
                    st.session_state.miss = True
                else:
                    if self._valid_pwd(st.session_state.in_login, pwd):
                        st.session_state.auth_status = True
                        st.session_state.super = \
                                      self._is_admin(st.session_state.in_login)
                        st.session_state.login = st.session_state.in_login
                        placeholder.empty()
                    else:
                        st.session_state.auth_status = False


    def _update_pwd(self, i_login, pwd, status='temp'):
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
        up_pwd_sql ="UPDATE my_user SET status=%(status)s, pwd=%(hsh_pwd)s \
                     WHERE login=%(login)s;"
        # Query database
        self.cursor.execute(up_pwd_sql,
                            {'status':status, 'hsh_pwd':hsh_pwd,
                             'login':i_login})


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
        bool.

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

        forgot_password_form = st.form('Forgot_Password')


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
                    email = self.get_email(v_login)
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

    def _get_login(self, i_email):
        """
        get login of user cause email

        Parameters
        ----------
        i_email : TYPE
            DESCRIPTION.

        Returns
        -------
        str
           login of user

        """
        login_email_sql = """SELECT login, email FROM my_user
                             WHERE email ~* %(start_email)s"""
        start_email = '^' + i_email[0]
        self.cursor.execute(login_email_sql, {'start_email':start_email})
        l_login_email_pwd = self.cursor.fetchall()
        # Check if email exist
        for user in l_login_email_pwd:
            if user[1] == i_email:
                return user[0]
        return None


    def forgot_login(self):
        """
        Send login of user.

        """

        forgot_password_form = st.form('Forgot_Login')


        forgot_password_form.subheader(_('title_forgot_login'))
        forgot_password_form.text_input(_('forgot_login_email'),
                                        key='v_forgot_login')

        st.session_state['state_forgot_login'] = 3

        def inside():
            v_email = st.session_state.v_forgot_login
            # Thx https://stackoverflow.com/a/5063991
            regex_no_empty = r'[^$^\ ]'
            if not re.match(regex_no_empty, v_email) is None :
                v_login = self._get_login(v_email)
                if not v_login is None:

                    st.session_state['state_forgot_login'] = 0

                    # Send login by email
                    send_email(dst=v_email, sub=_('msg_email_sub_login'),
                               msg=_('msg_email_header_login') + v_login +
                                   _('msg_email_end'))

                else:
                    st.session_state['state_forgot_login'] = 1
            else:
                st.session_state['state_forgot_login'] = 2

            del st.session_state.v_forgot_login


        forgot_password_form.form_submit_button(_('bt_forgot_login_submit'),
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
            del st.session_state.login

        st.sidebar.button(_('bt_logout'), help=_('bt_logout_help'),
                          on_click=inside)

    def update_email(self, i_login, email, where_msg):
        """


        Parameters
        ----------
        i_login : TYPE
            DESCRIPTION.
        email : TYPE
            DESCRIPTION.
        where_msg : TYPE, optional
            DESCRIPTION. The default is None.

        Returns
        -------
        None.

        """
        if(valid_email(i_login, email, where_msg) and
           self._valid_login(i_login)):
            up_email_sql = '''UPDATE my_user
                              SET email=%(email)s
                              WHERE login=%(login)s'''

            self.cursor.execute(up_email_sql, {'email':email, 'login':i_login})

            where_msg.success(_('msg_update_email'))

    def update_pwd(self, where_display):
        """


        Returns
        -------
        None.

        """
        login_form = where_display.form('up_pwd')

        login_form.subheader(_('title_form_up_pwd'))
        login_form.text_input(_('form_pwd_current'), type='password',
                              key= 'current_pwd')
        login_form.text_input(_('form_pwd_new'), type='password',
                              key='new_pw_0')
        login_form.text_input(_('form_pwd_conf'), type='password',
                              key=' new_pw_1')

        def inside():
            current_pwd = st.session_state.current_pwd
            new_pwd = [st.session_state.new_pw_0, st.session_state.new_pw_0]
            ### Verify input not empty
            # Thx https://stackoverflow.com/a/5063991
            regex_no_empty = r'[^$^\ ]'
            where_display.write(current_pwd)
            where_display.write(new_pwd)
            where_display.write(keyword_inside(new_pwd[1]))
            # Check if current pwd is correct, new pwd is same twice,
            # new pwd not empty and no keyword of sql in pwd
            if (self._valid_pwd(st.session_state.login, current_pwd) and
                new_pwd[0] == new_pwd[1] and
                not re.match(regex_no_empty, new_pwd[1]) is None and
                not keyword_inside(new_pwd[1])):

                self._update_pwd(st.session_state.login, new_pwd[0], '')

                where_display.success(_('msg_up_pwd_ok'))

            else:
                where_display.error(_('msg_up_pwd_fail'))


        login_form.form_submit_button(_('bt_login_submit'), on_click=inside)


def vide():
    """
    empty function

    Returns
    -------
    None.

    """

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
        if st.button(_('bt_forgot_login'), help=_('bt_forgot_login_help')):
             st.session_state.authr.forgot_login()


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
            st.success(_('msg_forgot_pwd_ok'))
        del st.session_state.state_forgot_pwd

    if 'state_forgot_login' in st.session_state:
        if st.session_state.state_forgot_login == 1 :
            st.error(_('msg_forgot_login_fail'))
        elif st.session_state.state_forgot_login == 2:
            st.info(_('msg_forgot_login_miss'))
        elif st.session_state.state_forgot_login == 0:
            st.success(_('msg_forgot_login_ok'))
        del st.session_state.state_forgot_login

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
