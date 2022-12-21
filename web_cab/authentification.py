#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Oct 27 11:22:18 2022

@author: mpalerme
"""
import os
import sys
sys.path.append(os.path.dirname(__file__))
import re
from translate import _
import streamlit as st
from my_email import send_email
import bcrypt
import numpy as np
import csv
import connect as ct

def gen_word():
    """
    generated a word

    Returns
    -------
    str.

    """
    # Define size of password
    size_pwd = np.random.randint(12, 31)
    type_pwd = np.dtype((str, size_pwd))

    # Generate a password (32 in Ascii is Space and 126 is ~)
    return np.random.randint(low=32, high=126, size=size_pwd,
                             dtype="int32").view(type_pwd)[0]

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
        if ((key[0] + ' ').upper() in sentence.upper() or
            (' ' + key[0]).upper() in sentence.upper()):
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

    def _temporary(self, i_login):
        """
        Indicate if pwd of user is temporary

        Returns
        -------
        bool.
            True : pwd temporary

        """
        if(self._valid_login(i_login)):
            temp_pwd_sql = """SELECT (CASE WHEN status = 'temp'  OR
                                             status = 'temp_super'
                                        THEN 1 ELSE 0 END) AS admin
                              FROM my_user WHERE login = %(login)s;
                          """
            self.cursor.execute(temp_pwd_sql, {'login': i_login})

            if self.cursor.fetchone()[0] == 1:
                return True

        return False


    def login(self):
        """
        Creates a login widget.

        """
        st.session_state['miss'] = False
        st.session_state['temp_pwd'] = False
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
                        st.session_state.temp_pwd = \
                                     self._temporary(st.session_state.in_login)
                        placeholder.empty()
                    else:
                        st.session_state.auth_status = False


    def _update_pwd(self, i_login, pwd, status):
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
        up_pwd_sql ="""UPDATE my_user SET status=%(status)s, pwd=%(hsh_pwd)s
                       WHERE login=%(login)s;
                    """
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
        # Generate a word
        pwd = gen_word()

        # Indicate pwd is temporary and next connection of user. It'll have to
        # change pwd
        v_status = 'temp'
        if self._is_admin(i_login) is True:
            v_status = 'temp_super'

        # save Hashed password
        self._update_pwd(i_login, pwd, v_status)

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

        # Verify if we find login
        if l_login_pwd is None:
            return False

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

    def change_pwd(self, where_display):
        """
        provide form to modify pwd

        where_display : streamlit object
            where write message.

        Returns
        -------
        None.

        """
        login_form = where_display.form('up_pwd')

        login_form.subheader(_('title_form_up_pwd'))
        login_form.text_input(_('form_pwd_current'), type='password',
                              key= 'current_pwd')
        login_form.text_input(_('form_pwd_new'), type='password',
                              key='new_pwd_0')
        login_form.text_input(_('form_pwd_conf'), type='password',
                              key='new_pwd_1')

        def inside():
            """
            process of change pwd

            Returns
            -------
            None.

            """
            if ('current_pwd' in st.session_state and
                'new_pwd_0' in st.session_state and
                'new_pwd_1' in st.session_state):

                current_pwd = st.session_state.current_pwd
                new_pwd = [st.session_state.new_pwd_0, st.session_state.new_pwd_1]
                ### Verify input not empty
                # Thx https://stackoverflow.com/a/5063991
                regex_no_empty = r'[^$^\ ]'

                # Check if current pwd is correct, new pwd is same twice,
                # new pwd not empty and no keyword of sql in pwd
                if (self._valid_pwd(st.session_state.login, current_pwd) and
                    new_pwd[0] == new_pwd[1] and
                    not re.match(regex_no_empty, new_pwd[1]) is None and
                    not keyword_inside(new_pwd[1])):

                    # Keep status administrateur or not
                    v_super = ''
                    if st.session_state.super is True:
                        v_super = 'super'

                    # change pwd of user
                    self._update_pwd(st.session_state.login, new_pwd[0],
                                     v_super)

                    where_display.success(_('msg_up_pwd_ok'))

                else:
                    print('why')
                    where_display.error(_('msg_up_pwd_fail'))
            else:
                where_display.info(_('msg_up_pwd_miss'))
            # Delete of session all pwd
            if 'current_pwd' in st.session_state:
                del st.session_state.current_pwd
            if 'new_pwd_0' in st.session_state:
               del st.session_state.new_pwd_0
            if 'new_pwd_1' in st.session_state:
               del st.session_state.new_pwd_1


        login_form.form_submit_button(_('bt_login_submit'), on_click=inside)

    def _get_users(self):
        """
        give list of all user

        Returns
        -------
        list of str.

        """
        # Define query
        users_sql = "SELECT login FROM my_user;"

        # Query database
        self.cursor.execute(users_sql)

        # Give the list
        return [user[0] for user in self.cursor.fetchall()]


    def create_user(self, where_display):
        """
        Create a user

        Parameters
        ----------
        where_display : TYPE
            DESCRIPTION.

        Returns
        -------
        None.

        """
        create_form = where_display.form('create_user')

        create_form.subheader(_('title_form_create_user'))

        create_form.text_input(_('form_create_user_login'), key='cu_login')
        create_form.text_input(_('form_create_user_email'), key='cu_email')
        create_form.checkbox(_('form_create_user_admin'), key='cu_super')

        def inside():
            """
            process of create user

            Returns
            -------
            None.

            """
            ### Verify input not empty
            # Thx https://stackoverflow.com/a/5063991
            regex_no_empty = r'[^$^\ ]'

            if('cu_email' in st.session_state and
               'cu_login' in st.session_state and
               'cu_super' in st.session_state and
               not re.match(regex_no_empty, st.session_state.cu_login)
                    is None and
               not re.match(regex_no_empty, st.session_state.cu_email)
                    is None):
                # Check if login doesn't exist yet
                print(self._get_users())
                if st.session_state.cu_login in self._get_users():
                    where_display.info(_('msg_create_user_exist'))
                else:
                    if(valid_email(st.session_state.cu_login,
                                   st.session_state.cu_email,
                                   where_display)):
                        # Define query to create use
                        cu_sql = """ INSERT INTO my_user
                                     VALUES (%(login)s, %(email)s, %(fake)s,
                                             %(status)s);
                                 """
                        # Create user in database
                        self.cursor.execute(cu_sql,
                        {'login':st.session_state.cu_login,
                         'email':st.session_state.cu_email,
                         'fake':gen_word(),
                         'status':'super' if st.session_state.cu_super else ''}
                                           )

                        # send email to new user
                        send_email(st.session_state.cu_email,
                                   _('msg_email_sub_create_user'),
                                   _('msg_email_header_create_user') +
                                   st.session_state.cu_login +
                                   _('msg_email_end'))

                        where_display.success(_('msg_create_user_ok'))
            else:
                where_display.info(_('msg_create_user_miss'))

        create_form.form_submit_button(_('bt_create_user_submit'),
                                       on_click=inside)

    def delete_user(self, where_display):
        """
        delete a user

        Returns
        -------
        None.

        """
        # Remove login of admin
        l_users = self._get_users()
        del l_users[l_users.index(st.session_state.login)]

        # Verify if there are user
        if l_users is None:
            where_display.write(_('msg_no_user'))

        # Select all user except the user
        sbx_user= where_display.selectbox(_('cbx_delete_user'), l_users)
        where_display.text(_('label_login') + ' : ' + sbx_user)
        where_display.text(_('label_email') + ' : ' + self.get_email(sbx_user))


        if(where_display.button(_('bt_del_user_submit'))):
            conf_form = where_display.form('conf_delete')
            # confirm delete by write email of deleted user
            conf_form.text_input(_('label_confirm_del_user'), key='email_conf')

            def inside():
                """
                process to delete a user

                Returns
                -------
                None.

                """
                if st.session_state.email_conf == self.get_email(sbx_user):

                    # Define query to delete user
                    del_user_sql = """ DELETE FROM my_user
                                       WHERE login=%(login)s
                                       AND email=%(email)s;
                                   """
                    # Query database
                    self.cursor.execute(del_user_sql,{'login':sbx_user,
                                                      'email':st.session_state.email_conf})

                    where_display.success(_('msg_del_user_ok'))
                else:
                    where_display.info(_('msg_del_user_mail_diff'))

            conf_form.form_submit_button(_('bt_confirm_del_user'),
                                         on_click=inside)


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
    if (not'browser' in st.session_state or
        st.session_state['browser'] is False):
        return vide

    # Connect to database
    cursor = ct.connect_dbb()
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
        if st.session_state.temp_pwd is True:
            authr.change_pwd(st)
        else:
            del st.session_state.temp_pwd
            v_return = function
    elif st.session_state.miss is True :
        st.info(_('msg_login_miss'))
    elif st.session_state.auth_status is False :
        st.error(_('msg_login_fail'))
    return v_return
