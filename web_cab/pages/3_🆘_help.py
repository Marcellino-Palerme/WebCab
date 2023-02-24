#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Dec 27 13:54:10 2022

@author: mpalerme

This page is web cab manual
"""
import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import streamlit as st
from translate import _, link, select_language
from custom import hide_hamburger
from browser import browser_ok
from notification import notif
from bs4 import BeautifulSoup
import base64


# Define title of page and menu
st.set_page_config(
    page_title=_('Title_help'),
    page_icon="🆘",
    layout="wide",
    initial_sidebar_state="auto"
)

select_language()

def rich_txt(html):
    """


    Parameters
    ----------
    html : TYPE
        DESCRIPTION.

    Returns
    -------
    None.

    """
    # Parse html
    parser = BeautifulSoup(html, 'html.parser')

    # image
    for image in parser.findAll('img'):
        img_file = open(os.path.abspath(os.path.join('.', 'web_cab', 'images',
                                                      image['src'])), "rb")
        # Extract extension of images
        extension = os.path.splitext(image['src'])[1][1:]
        contents = img_file.read()
        data_url = base64.b64encode(contents).decode("utf-8")
        img_file.close()
        image['src'] = "data:image/%s;base64,%s" %(extension, data_url)

    st.markdown(parser, True)


def create_contents(dict_section, index='', header=''):
    """
    create contents of page
    (recursive function)

    Parameters
    ----------
    dict_section : dictionnary of dictionnary
        DESCRIPTION.

    index : str
        Contain number of parent's section Default : ''

    header : str
        Contain level of hearder by # Default: ''

    Returns
    -------
    None.

    """

    if len(dict_section) > 0:
        num_section = 0
        for section in dict_section:
            # add content of section
            if section == '<txt>':
                rich_txt(dict_section[section])
            # Define Section
            else:
                num_section += 1
                temp_ind = "%s%s" %(index, num_section)
                temp_sec = "%s.%s" %(temp_ind, section)
                # Add section in summary
                st.sidebar.markdown('- '*len(header) + ' #' + header + ' ' + link(temp_sec))
                # Write header of setion
                st.markdown('#' + header + ' ' + temp_sec)
                # Write under-section
                create_contents(dict_section[section], temp_ind + '.',
                                '#' + header)

@notif(trans=_)
@browser_ok
@hide_hamburger
def page():
    """
    compose page

    Returns
    -------
    None.

    """
    dict_contents = {
        _('Title_help_summary') : {
            '<txt>' : _('Txt_help_summary_ht')},
        _('Title_help_quickstart') : {
            '<txt>' : _('Txt_help_quickstart_ht')},
        _('Title_help_upload') : {
            '<txt>' : _('Txt_help_upload_ht'),
            _('Title_help_up_input') : {
                '<txt>' : _('Txt_help_up_input_ht'),
                _('Title_help_archive') : {
                    '<txt>' : _('Txt_help_archive_ht')},
                _('Title_help_nb_barcode') : {
                    '<txt>' : _('Txt_help_nb_barcode_ht')},
                _('Title_help_valid_file') : {
                    '<txt>' : _('Txt_help_valid_file_ht')}},
            _('Title_help_up_output') : {
                '<txt>' : _('Txt_help_up_output'),
                _('Title_help_im_bar_csv') : {
                    '<txt>' : _('Txt_help_im_bar_csv_ht')},
                _('Title_help_rename_im') : {
                    '<txt>' : _('Txt_help_rename_im_ht')}}
            },
        _('Title_help_download') : {
            '<txt>' : _('Txt_help_download_ht')},
        _('Title_help_profile') : {
            '<txt>' : _('Txt_help_profile_ht')},
        _('Title_help_FAQ') : {
            '<txt>' : _('Txt_help_FAQ_ht'),
            _('Title_help_info_image'):{
                '<txt>':_('Txt_help_info_image')},
            _('Title_help_info_cb') : {
                '<txt>':_('Txt_help_info_cb')}}
        }

    create_contents(dict_contents)



    # upload part


if callable(page) :
    page()
