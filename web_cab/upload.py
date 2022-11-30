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

    # Define formulaire space
    my_form_temp = st.empty()
    my_form = my_form_temp.container()

    my_form.header(_('Upload_image'))
    # Title of input part
    in_part = my_form.expander( '**' + _('Input_part') + '**', True)
    # Upload button to zip
    up_file = in_part.file_uploader(_('Archive_with_images'), ['zip'], False)
    # Number of code barre maximum by images
    max_bar = in_part.number_input(_('Max_barcode_by_image'), min_value=1,
                                   value=1, step=1, format='%d')


    ### Choice depends of number of barcode by image
    choice_valid_file = [_('chk_used_valid_file'),
                         _('chk_not_used_valid_file')]
    if max_bar>1 :
        # If there are several barcode we need a validation file but you can
        # force to not used
        # Message to indicate it is better use validation file
        in_part.markdown('<span style="color: red;" class="enclosing"><i>' +
                         _('msg_use_validation_file') + '</i></span>', True)
        # Choice use or not validation file
        bt_valid_file = in_part.radio(_('radio_valid_file'), choice_valid_file,
                                      horizontal=True,
                                      label_visibility='hidden')
    else:
        # Part we validation file is optional
        bt_valid_file = in_part.checkbox(_('chk_used_valid_file'))

    # Provide part to upload validation if ask
    if (bt_valid_file is True) or (bt_valid_file == choice_valid_file[0]):
        # Upload button to validation file
        up_csv = in_part.file_uploader(_('Validation_file'), ['csv'], False)

    # Title of output part
    out_part = my_form.expander('**' +_('Output_part') + '**', True)
    # Select a output csv file
    out_csv = out_part.checkbox(_('link_image_barcode_file'), value=True)

    ### Select format of rename image
    cols = out_part.columns([1,3])
    bt_out_format = cols[0].checkbox(_('Rename_image'))
    if bt_out_format:
        lt_format = (_('only_barcode'), _("Image_name_barecode"),
                     _("barecode_image_name"))

        cols[1].write('')
        f_rn = cols[1].radio(_("format_image_name"), lt_format)

    ### Process formular
    if my_form.button(_('bt_upload_submit')):
        # Get name of image without special caracters
        im_name = re.sub('[^\.a-zA-Z0-9]', '_', up_file.name)
        # Save last image name
        st.session_state.update({'im_name':im_name})
        # show name image
        st.write(im_name)
        # show image
        raw_data = up_file.getvalue()

        ### Extract zip
        # Create one directory
        my_uuid = str(uuid.uuid4())
        dir_extract = os.path.join(path_temp, my_uuid)
        os.makedirs(dir_extract)
        os.makedirs(dir_extract + '_temp')

        # save zip
        with open(os.path.join(dir_extract, im_name),'wb') as out_f:
            out_f.write(raw_data)

        ### Define option for cab
        options = '-n ' + str(max_bar)

        if (bt_valid_file is True) or (bt_valid_file == choice_valid_file[0]):
            # save validation file
            with open(os.path.join(dir_extract, up_csv.name),'wb') as out_val:
                out_val.write(up_csv.getvalue())
            # add to option using validation file
            options = options + ' -v ' + os.path.join(dir_extract, up_csv.name)

        # Add to options output in csv
        if out_csv:
            options = options + ' -c'

        # Add to option rename image
        if bt_out_format:
            if f_rn == lt_format[0]:
                options = options + ' -b'
            if f_rn == lt_format[1]:
                options = options + ' -s'
            if f_rn == lt_format[2]:
                options = options + ' -p'

        # Define query add inpus
        add_in_sql = """ INSERT INTO inputs (uuid, login, size, state, upload,
                                             options)
                         VALUES (%(uuid)s, %(login)s, %(size)s, 0,
                                 CURRENT_TIMESTAMP,%(options)s);
                     """

        st.session_state['cursor'].execute(add_in_sql,
                                           {'uuid':my_uuid,
                                            'login':st.session_state.login,
                                            'size':sys.getsizeof(raw_data),
                                            'options':options})

        # Run in background cab
        thd_bgd = Thread(target=bgd.launcher)
        thd_bgd.start()

        # Explain result
        st.info(_('Id of your process: ') + my_uuid)
        st.write(_('msg_success_upload'))

        my_form_temp.empty()

        st.stop()


if callable(run) :
    run()
