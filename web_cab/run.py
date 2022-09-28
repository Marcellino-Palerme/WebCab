#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Sep 28 09:39:45 2022

@author: Marcellino Palerme
"""
import streamlit as st
from PIL import Image


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

st.title("Test streamlit")

st.subheader('Upload image')

# Upload button
up_file = st.file_uploader('votre image', ['png', 'jpg'], False)

if up_file is not None:
    # Get name of image
    im_name = up_file.name
    # show name image
    st.write(im_name)
    # show image
    raw_data = up_file.getvalue()
    st.image(raw_data)

    # save image
    with open("/mnt/stockage/temp/test.png",'wb') as out_f:
        out_f.write(raw_data)

if st.button('En gris'):
    # Read image
    my_image = Image.open("/mnt/stockage/temp/test.png")
    # Convert to grey
    my_image = my_image.convert('L')
    # Show gray image
    st.image(my_image)
