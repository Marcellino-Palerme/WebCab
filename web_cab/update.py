#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on 2023 - 02 - 07

@author: mpalerme


"""
import time
import os
import sys
import subprocess
import psutil
import shutil
import json

sys.path.append(os.path.dirname(__file__))
from connect import connect_dbb
from my_email import send_email
from translate import _


def check_up():
    """
    Verify if new version of web cab is avaible
    """

    ### Check if update or upgrade
    # Define query to know if up* will program
    nb_up_sql = """ SELECT COUNT(when) FROM wc_up; """

    # Connect to database
    cursor = connect_dbb()

    # Query database
    cursor.execute(nb_up_sql)

    nb_up = cursor.fetchone()[0]
    # No up* will program yet
    if nb_up == 0:
        # Check branch used update
        the_up = subprocess.check_output(['git', 'pull', '--dry_run'])
        if len(the_up)>2:
            # Define query to indicate new update
            add_up = """UPDATE wc_up
                        SET when=CURRENT_TIMESTAMP + interval ' 1 days',
                            date_grade=0;
                     """

            # Query database
            cursor.execute(add_up)

            # Close connexion
            cursor.close()
            # A update on branch
            return True

        # Close connexion
        cursor.close()
        # No update on branch
        return False

    # Close connexion
    cursor.close()
    # Update in preparing yet
    return True

def stop():
    """
    Stop Web Cab

    Returns
    -------
    str to indicate part stoppping (front / back)

    """
    ### Check where it is, front or back -end
    path_back = os.path.join(os.path.dirname(__file__), 'conf', 'back.json')

    if os.path.exists(path_back):
        # Get PID of background.py
        with open(path_back, 'r', encoding='utf-8') as jback:
            pid = json.load(jback)['PID']

        # kill process
        os.system('kill -9 ' + str(pid))

        # Delete json indicating PID of background
        os.remove(path_back)

        return 'back'
    else:
        # kill streamlit
        os.system('pgrep streamlit | xargs kill -9')
        return 'front'


def update():
    """
    Stop Web Cab
    Update Web Cab
    Restart Web Cab
    Notify administrator update done

    Returns
    -------
    None.

    """
    # Stop Web Cab
    part = stop()

    # Update
    os.system('git pull')

    # Restart Web Cab
    if part == 'back':
        path_bg = os.path.join(os.path.dirname(__file__), 'background.py')
        subprocess.Popen('python', path_bg)
    else:
        path_wc = os.path.join(os.path.dirname(__file__), '..')
        path_wc = os.path.abspath(path_wc)
        path_wc = os.path.join(path_wc, 'web_cab', '1_📥_upload.py')
        subprocess.Popen('python', 'streamlit', 'run',
                         '--browser.gatherUsageStats', 'false', path_wc)

    ### Notify
    ## Get email of admins

    # Define query to get email of admins
    mail_admin_sql = """ SELECT email FROM my_user
                         WHERE state = 'super' OR state = 'temp_super';
                     """

    # Connect to database
    cursor = connect_dbb()

    # Query database
    cursor.execute(mail_admin_sql)

    for mail in cursor.fetchall():
        send_email(mail, sub=_('msg_email_sub_update'),
                   msg=_('msg_email_header_update') + '\r\n\r\n' + part +
                         '\r\n\r\n' + _('msg_email_end'))

def upgrade():
    """
    Stop Web Cab
    Save database
    Notify administrator can upgrade

    Returns
    -------
    None.

    """
    # Stop Web Cab
    if stop() == 'back':
        # Only back can save database
        # Connect to database
        cursor = connect_dbb()

def scheduler():
    """


    Returns
    -------
    None.

    """


    while(True):

        if check_up():
            # Define query to know date of futur up*
            date_up_sql = """SELECT date_grade FROM wc_up
                             WHERE when < CURRENT_TIMESTAMP
                             ORDER BY when;
                          """
            # Connect to database
            cursor = connect_dbb()

            # Query database
            cursor.execute(date_up_sql)

            # Get early update
            date_up = cursor.fetchone()

            # Check if we have to up*
            if not date_up is None:
                # Verify if is update
                if date_up[0] is False:
                    update()
                else:
                    upgrade()
                    # Stop process
                    break
        # Wait 1 days
        time.sleep(60*60*24)




if __name__ == "__main__":

    scheduler()
