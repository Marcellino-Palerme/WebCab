#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Oct 27 11:22:18 2022

@author: mpalerme
"""
import json
import gettext as gt
import psycopg2 as pc2
import streamlit as st
import streamlit_authenticator as sta
from streamlit_javascript import st_javascript as stj
from web_cab.email import send_email
from datetime import datetime, timedelta

gt.bindtextdomain('web_cab', '/path/to/my/language/directory')
gt.textdomain('web_cab')
_ = gt.gettext

class My_Authen(sta.Authenticate):

    def __init__(self, credentials, cookie_name, key, expiry_day):
        sta.Authenticate.__init__(self, credentials, cookie_name, key,
                                  cookie_expiry_days=expiry_day)


    def get_email(self, username):
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
        if username in self.credentials['usernames']:
            return self.credentials['usernames'][username]['email']
        else:
            return False

    def update_name(self, username, name):
        """
        Update name user

        Parameters
        ----------
        username : str
            login of user.
        name : str
            Name user.

        Returns
        -------
        None.

        """
        st.session_state.name = name
        self.exp_date = self._set_exp_date()
        self.token = self._token_encode()
        self.cookie_manager.set(self.cookie_name, self.token,
                                 expires_at=datetime.now() +\
                                      timedelta(days=self.cookie_expiry_days))
        self._update_entry(username, 'name', name)

    def update_email(self, username, email):
        """


        Parameters
        ----------
        username : str
            login of user.
        email : str
            New email of user.

        Returns
        -------
        None.

        """
        self._update_entry(username, "email", email)

def vide():
    """
    empty function

    Returns
    -------
    None.

    """
    pass

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

def forgot_pwd():
    """
    send a temporary password

    Returns
    -------
    None.

    """
    # Generated a temporary password
    forgot_status, email, pwd = st.session_state.authr.forgot_password(
                                _('title_forgot_pwd'))

    if forgot_status :
        ### Modify user password
        # query for modification
        up_pwd_sql ='''UPDATE my_user
                       SET status=temp
                       SET pwd=''' + sta.Hasher(pwd) + \
                    '''WHERE email=''' + email + ';'
        # Query database
        st.session_state.cursor.execute(up_pwd_sql)

        # Send temporary email
        send_email(dst=email, sub=_('msg_email_sub_pwd'),
                   msg=_('msg_email_header_pwd') + pwd + _('msg_email_end') )

        st.success(_('msg_forgot_pwd_send'))

    elif forgot_status is False:
        st.error(_('msg_forgot_pwd_fail'))

    elif forgot_status is None:
        st.info(_('msg_forgot_pwd_miss'))


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

        st.success(_("msg_forgot_login_sent"))

    elif forgot_status is False :
        st.error(_('msg_forgot_login_fail'))

    elif forgot_status is None :
        st.info(_('msg_forgot_login_miss'))

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
        st.button(_('bt_forgot_pwd'), help=_('bt_forgot_pwd_help'), on_click=
                  forgot_pwd)
    with a_col[1]:
        st.button(_('bt_forgot_login'), help=_('bt_forgot_login_help'), on_click=
                  forgot_login)


def check_input(field):
    """


    Parameters
    ----------
    field : TYPE
        DESCRIPTION.

    Returns
    -------
    None.

    """
    result = stj('''
                    alert(result);
                 ''')
    st.write(result)
    return result

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

    # create query
    user_info_sql = '''SELECT login, name, email, pwd
                       FROM my_user;'''

    # query database
    cursor.execute(user_info_sql)
    l_user = cursor.fetchall()

    # Formating dictionnary
    d_user = {"usernames":{user[0]:{'email':user[2],
                                    'name':user[1],
                                    'password':user[3]}} for user in l_user}

    ### Manage sign in
    # initiate login widget
    authr = My_Authen(d_user,d_conf['cookie']['name'], d_conf['cookie']['key'],
                      d_conf['cookie']['expiry_day'])

    # Save obj in session
    st.session_state['authr'] = authr

    # Show widget login
    authr.login(_('title_login'), 'main')

#     stj('''var d_fied = { Username= 0, Password = 0};

# function check(field, bt){
#                var labels = document.getElementsByTagName('label');
#                for(var i=0; i<labels.length; i++){
#                   if(labels[i].textContent ==  field ){
#                      var div = labels[i].parentElement;
#                   }
#                }
#                var input = div.getElementsByTagName('input')[0];
#                d_fied[field] = 1
#                if (input.value == ""){
#                   d_fied[field] = 0;
#                 }
#                if(d_fied.Username + d_fied.Password > 1){bt.disabled=true}
#   else{bt.disabled=false}
#             }

# function add_oninput(field, bt){
#                var labels = document.getElementsByTagName('label');
#                for(var i=0; i<labels.length; i++){
#                   if(labels[i].textContent ==  field ){
#                      var div = labels[i].parentElement;
#                   }
#                }
#                var input = div.getElementsByTagName('input')[0];
#                input.oninput = check(field, bt);
#             }

# if(check('Username')==0 & check('Password')==0){
# var bt = document.getElementsByTagName('button')
#            for(var i=0; i<bt.length; i++){
#               if(bt[i].textContent == 'Login'){
#                  var res = bt[i]
#               }
#            }
# res.disabled=true
# }
# else
#  {
#    res.disabled=false
#  }

# add_oninput("Username", res)
# add_oninput("Password", res)

#         ''')

    # Add buttons for forgot password or login
    forgot()
    v_return = vide
    st.write(st.session_state.authentication_status)
    if st.session_state.authentication_status :
        # add acces profile and logout on sidebar
        authr.logout(_('bt_logout'), 'sidebar')
        v_return = function
    elif st.session_state.authentication_status is False :
        # if int(stj('''check_empty;''')) > 0:
        #     st.error(_('msg_login_fail'))
        # else:
        #     st.info(_("msg_login_miss"))
        st.error(_('msg_login_fail'))
    return v_return
