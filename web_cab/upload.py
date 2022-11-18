#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Sep 28 09:39:45 2022

@author: Marcellino Palerme

First app with streamlit
This app :
    - Upload image png or jpg
    - Show it
    - Convert to grayscale
    - Show it
    - Download grayscale image
"""
import os
import sys
sys.path.append(os.path.dirname(__file__))
import streamlit as st
import re
from authentification import login
from translate import _
import uuid
from browser import browser_ok
import background as bgd
from threading import Thread


# Define title of page and menu
st.set_page_config(
    page_title="Test streamlit",
    page_icon="random",
    layout="wide",
    initial_sidebar_state="auto",
    menu_items={
        'Get Help': 'https://lesjoiesducode.fr/quand-on-na-pas-fourni-de-doc-aux-utilisateurs',
        'Report a bug': "https://forgemia.inra.fr/demecologie/web-cab/-/issues",
        'About': "first streamlit app"
    }
)

@login
@browser_ok
def run():

    # Define where save Uploaded image
    path_temp = os.path.join(os.path.dirname(__file__), 'temp')
    os.makedirs(path_temp, exist_ok=True)

    st.subheader('Upload image')

    up_form = st.form('upload_form')
    # Upload button to zip
    up_file = up_form.file_uploader('votre image', ['zip'], False)

    if up_form.form_submit_button(_('bt_upload_submit')):
        # Get name of image without special caracters
        im_name = re.sub('[^\.a-zA-Z0-9]', '_', up_file.name)
        # Save last image name
        st.session_state.update({'im_name':im_name})
        # show name image
        st.write(im_name)
        # show image
        raw_data = up_file.getvalue()
        # st.image(raw_data, width=200)

        ### Extract zip
        # Create one directory
        my_uuid = str(uuid.uuid4())
        dir_extract = os.path.join(path_temp, my_uuid)
        os.makedirs(dir_extract)
        os.makedirs(dir_extract + '_temp')

        # save zip
        with open(os.path.join(dir_extract, im_name),'wb') as out_f:
            out_f.write(raw_data)

        # Define query add inpus
        add_in_sql = """ INSERT INTO inputs
                         VALUES (%(uuid)s, %(login)s, %(size)s, 0,
                                 CURRENT_TIMESTAMP);
                     """

        st.session_state['cursor'].execute(add_in_sql, {'uuid':my_uuid,
                                                        'login':st.session_state.login,
                                                        'size':sys.getsizeof(raw_data)})

        st.session_state['dir_extract'] = dir_extract
        thd_bgd = Thread(target=bgd.launcher)
        thd_bgd.start()

        st.info(_('Id of your process: ') + my_uuid)



run()
