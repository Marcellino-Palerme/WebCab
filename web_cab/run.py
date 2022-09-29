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
import streamlit as st
import os
from PIL import Image

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

# Define where save Uploaded image
path_temp = '/mnt/stockage/temp'

st.subheader('Upload image')

# Upload button
up_file = st.file_uploader('votre image', ['png', 'jpg'], False)
# State to know if we loaded a image
b_up_file = up_file is not None
if b_up_file:
    # Get name of image
    im_name = up_file.name
    # Save last image name
    st.session_state.update({'im_name':im_name})
    # show name image
    st.write(im_name)
    # show image
    raw_data = up_file.getvalue()
    st.image(raw_data, width=200)

    # save image
    with open(os.path.join(path_temp, im_name),'wb') as out_f:
        out_f.write(raw_data)

    # Add button to convert image and converted image
    if st.button('En gris') or 'show' in list(st.session_state.keys()):
        # Read image
        my_image = Image.open(os.path.join(path_temp, im_name))
        # Convert to grey
        my_image = my_image.convert('L')
        # Show gray image
        st.image(my_image, width=200)
        # Variable to keep the ploting of image after download it
        st.session_state.update({'show':True})
        # save grayscale image
        with open(os.path.join(path_temp, 'gray_' + im_name), 'wb') as out_f:
            my_image.save(out_f)

        # Button to download grayscale image
        with open(os.path.join(path_temp, 'gray_' + im_name), 'rb') as in_f:
            st.download_button('Télécharger l\'image en niveau de gris',
                               data=in_f, file_name='gray_'+ im_name,
                               mime=up_file.type,
                               help="cliquer pour récupérer l'image ci-dessus")
# To hide gray button, grayscale image and download button
# when delete or change image
if 'show' in list(st.session_state.keys()) and not b_up_file:
    # Change state to don't plot converted image
    del st.session_state.show
    # Delete converted image
    os.remove(os.path.join(path_temp, 'gray_' + st.session_state.im_name))

# Delete image saved
if 'im_name' in list(st.session_state.keys()) and not b_up_file:
    os.remove(os.path.join(path_temp, st.session_state.im_name))
    # Delete just to clear my session
    del st.session_state.im_name
