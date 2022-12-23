#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Sep 28 09:39:45 2022

@author: Marcellino Palerme

page to download processing images
"""
import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import streamlit as st
from authentification import login
from translate import _
from datetime import timedelta
from browser import browser_ok
from init_bdd import check_init
import shutil


# Define title of page and menu
st.set_page_config(
    page_title=_('Title_down'),
    page_icon="📤",
    layout="wide",
    initial_sidebar_state="auto",
    menu_items={
        'Get Help': _('http://URL_down_help'),
        'Report a bug': _('http://URL_down_bug'),
        'About': _('txt_about')
    }
)

def up_download(uuid):
    """
    Indicate result donwloaded

    Parameters
    ----------
    uuid : str
        Id of input.

    Returns
    -------
    None.

    """
    # Define query
    up_down_sql = """UPDATE inputs SET download=true
                     WHERE uuid=%(uuid)s;
                  """
    # Query database
    st.session_state.cursor.execute(up_down_sql, {'uuid':uuid})

def delete_input(uuid, path_temp):
    """
    delete the input

    Parameters
    ----------
    uuid : str
        Id of input.

    path_temp : str
        Where save inputs

    Returns
    -------
    None.

    """
    # Define query
    delete_sql = """ DELETE FROM inputs WHERE uuid=%(uuid)s;"""

    # Query database
    st.session_state.cursor.execute(delete_sql, {'uuid':uuid})

    os.remove(os.path.join(path_temp, uuid + '.zip'))
    shutil.rmtree(os.path.join(path_temp, uuid))
    shutil.rmtree(os.path.join(path_temp, uuid + '_temp'))

@login
@browser_ok
@check_init
def page():
    """
    compose page

    Returns
    -------
    None.

    """
    ### Get all processing of user
    # Define query
    user_proc_sql = """ SELECT uuid, state, upload, update, download
                        FROM inputs
                        WHERE login=%(login)s ORDER BY upload;
                    """
    # Query database
    st.session_state.cursor.execute(user_proc_sql,
                                    {'login':st.session_state.login})

    path_temp = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    path_temp = os.path.join(path_temp,'temp')

    ### TODO check if there are process

    lt_process = st.session_state.cursor.fetchall()

    # Verify if user have process
    if len(lt_process) > 0 :
        cols = st.columns([2,1])
        cols[0].write(_('msg_explain_ddl_page'))
        # Legend
        cols[1].markdown("""
                            <table>
                              <tr>
                                <td>""" + _('title_legend') + """</td>
                              </tr>
                              <tr>
                                <td>⏳ """ + _('legend_wait')+"""<br/>
                                    🔬 """ + _('legend_in_progress') +"""<br/>
                                    🏁 """ + _('legend_finish') +"""<br/>
                                </td>
                              </tr>
                            </table>
                            <br/>
                         """,True)
    else:
        st.write(_('no_process'))

    for uuid in lt_process:

        if 0<uuid[1]<100:
            with st.expander('🔬 ' + uuid[0] + _(' upload: ') +
                             uuid[2].strftime('%a %d %b %Y, %H:%M'),
                             expanded=False):
                st.progress(int(uuid[1]))
        elif uuid[1] == 0:
            with st.expander('⏳ ' + uuid[0] + _(' upload: ') +
                             uuid[2].strftime('%a %d %b %Y, %H:%M'),
                             expanded=False):
                st.text(_('Waiting'))
                st.markdown(':x:')
        elif uuid[1] == 100:
            with st.expander('🏁 ' + uuid[0] + _(' upload: ') +
                             uuid[2].strftime('%a %d %b %Y, %H:%M'),
                             expanded=False):
                st.text(_('Expiring: ') +
                        (uuid[3] +
                         timedelta(days=2)).strftime('%a %d %b %Y, %H:%M'))
                cols = st.columns([5, 1])
                with open(os.path.join(path_temp, uuid[0] + '.zip'),
                          "rb") as zp_f:
                    cols[0].download_button(_('download'), zp_f,
                                            uuid[0] + '.zip',
                                            'application/zip',
                                            on_click=up_download,
                                            args=[uuid[0],])
                    # Add button to delete process
                    cols[1].button(_('bt_delete_process'),
                                   on_click=delete_input,
                                   args=[uuid[0], path_temp],
                                   disabled=not uuid[4], key=uuid[0])

if callable(page) :
    page()
