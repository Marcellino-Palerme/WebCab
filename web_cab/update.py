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
    nb_up_sql = """ SELECT COUNT(soon) FROM wc_up; """

    # Connect to database
    cursor = connect_dbb()

    # Query database
    cursor.execute(nb_up_sql)

    nb_up = cursor.fetchone()[0]
    # No up* will program yet
    if nb_up == 0:
        # Check branch used update
        the_up = subprocess.check_output(['git', 'pull', '--dry-run'])
        if len(the_up)>2:
            # Define query to indicate new update
            add_up = """INSERT INTO wc_up (soon, completion, date_grade)
                        VALUES (CURRENT_TIMESTAMP + interval ' 1 days',
                                CURRENT_TIMESTAMP + interval ' 1 days 2 hours',
                                false);
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

def dump_table(tab_name):
    """
    Get all rows of table

    Parameters
    ----------
    tab_name : str
        name of table.

    Returns
    -------
    list of dictionary.
        one line by record and record is a dictionary with name of field and it
        value
    """
    # Connect to database
    cursor = connect_dbb()

    # Get all record in table
    cursor.execute('SELECT * FROM %(tab_name)s;', {'tab_name': tab_name})

    a_record = []
    for record in cursor.fetchall():
        dic_temp = {}
        for index, column in enumerate(cursor.description):
            dic_temp[column[0]] = record[index]

        a_record.append(dic_temp)

    return a_record

def dump_tables(tabs_name):
    """
    Get all row of several tables

    Parameters
    ----------
    tabs_name : list of str
        list of name of table.

    Returns
    -------
    dictionary of list of dictionary.

    """
    dic_tabs = {}
    for tab_name in tabs_name:
        dic_tabs[tab_name] = dump_table(tab_name)

    return dic_tabs

def upgrade():
    """
    Stop Web Cab
    Save database
    Notify administrator can upgrade

    Returns
    -------
    None.

    """
    # Connect to database
    cursor = connect_dbb()
    # Stop Web Cab
    part = stop()
    if  part == 'back':
        # Only back can save database
        dic_db = dump_tables(['my_user', 'inputs'])
        # Save in file
        with open(os.path.join(os.path.dirname(__file__), 'conf', 'save.json'),
                  'w', encoding='utf-8') as jsave:
            json.dump(dic_db, jsave)

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
        send_email(mail, sub=_('msg_email_sub_upgrade'),
                   msg=_('msg_email_header_upgrade') + '\r\n\r\n' + part +
                         '\r\n\r\n' + _('msg_email_end'))


def scheduler():
    """


    Returns
    -------
    None.

    """

    ### Wait wc_up table created
    # Connect to database
    cursor = connect_dbb()

    exist_wc_up = False
    while not exist_wc_up:
        cursor.execute("""SELECT EXISTS(SELECT *
                                        FROM information_schema.tables
                                        WHERE table_name='wc_up')
                       """)
        exist_wc_up = cursor.fetchone()[0]

        time.sleep(1)


    while True:

        if check_up():
            # Define query to know date of futur up*
            date_up_sql = """SELECT date_grade FROM wc_up
                             WHERE soon < CURRENT_TIMESTAMP
                             ORDER BY soon;
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
