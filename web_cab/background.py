#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Nov  9 10:52:18 2022

@author: mpalerme


"""
from zipfile import ZipFile as zf
import runpy
import time
import os
import sys
from crontab import CronTab
import psutil
import subprocess

sys.path.append(os.path.dirname(__file__))
from connect import connect_dbb
from my_email import send_email
from translate import _


MAX_TIME_PROCESS = 1
DELAY_BETWEEN_PROCESS = 1
SIZE_PROCESS = 10 * 1024 * 1024  # 10MB


def unzip(uuid):
    """
    unzip

    Parameters
    ----------
    uuid : str
        name of directory with zip.

    Returns
    -------
    None.

    """
    path_temp = os.path.join(os.path.dirname(__file__), 'temp')

    # Define path of directory contain zip
    dir_zip = os.path.join(path_temp, uuid)
    # Define path where extract zip
    dir_extract = os.path.join(path_temp, uuid, 'extract')

    # Take name of zip
    zip_name = list(filter(lambda l_f: 'zip' in l_f, os.listdir(dir_zip)))[0]

    # create extract directory
    os.makedirs(dir_extract, exist_ok=True)

    # Open Zip
    with zf(os.path.join(dir_zip, zip_name),'r') as zip_f:
        # Extract zip
        zip_f.extractall(path=dir_extract)



def background(uuid):
    """
    processing image with cab

    Parameters
    ----------
    uuid : str
        name of directory with zip.

    Returns
    -------
    None.

    """
    # Verify stay CPU and RAM to process
    if (psutil.cpu_percent(1) < 90 and
        psutil.virtual_memory().available > SIZE_PROCESS):
        ### Stop CRON
        # Get cron table
        cron = CronTab(user=True)
        # Find used cron
        for job in cron:
            if uuid == job.comment:
                # Stop the cron
                cron.remove(job)
                cron.write()
                break

        # unzip
        unzip(uuid)

        # Connect of database
        cursor = connect_dbb()

        # Query to update database when processed image
        pi_sql = """UPDATE inputs SET state=%(state)s, update=CURRENT_TIMESTAMP
                    WHERE uuid=%(uuid)s;"""

        # Query get option
        option_sql = """ SELECT options FROM inputs WHERE uuid=%(uuid)s;"""

        ### Run Cab
        # Get binary of cab
        cab_bin = os.path.join(os.path.dirname(sys.executable), 'cab')
        # Define path of directory with input images
        path_in = os.path.join(os.path.dirname(__file__), 'temp', uuid,
                               'extract')
        # Define path where save result of cab
        path_out = os.path.join(os.path.dirname(__file__), 'temp',
                                uuid + '_temp')

        # Define option of cab
        cursor.execute(option_sql, {'uuid':uuid})
        options = ' -l -i ' + path_in + ' -o ' + path_out + ' ' + \
                  cursor.fetchone()[0]
        # launch cab
        os.system(cab_bin + options)

        ### TODO update status of cab
        cursor.execute(pi_sql, {'state':100, 'uuid':uuid})

        ### Zip result
        # Define option for command lin zipfile
        sys.argv[1] = '-c ' + os.path.join(os.path.dirname(__file__), 'temp',
                                           uuid) + '.zip ' + path_out
        sys.argv[1:] = sys.argv[1].split()
        # Run function zip of zipfile
        runpy.run_module('zipfile', run_name="__main__")
        ### Notify by user of end process
        ## Get email of owner
        # Define query
        email_sql = """ SELECT email FROM my_user
                        WHERE login=(SELECT login FROM inputs
                                     WHERE uuid=%(uuid)s);
                    """
        # Query database
        cursor.execute(email_sql, {'uuid':uuid})

        send_email(dst=cursor.fetchone()[0],sub=_('msg_email_sub_end_cab'),
                   msg=_('msg_email_header_end_cab') + '\r\n\r\n' + uuid +
                       '\r\n\r\n' + _('msg_email_end'))




def launcher():
    """
    launch all cron to process cab in different directory

    Returns
    -------
    None.

    """
    ### Take all CRON lauchned yet
    cron = CronTab(user=True)
    l_cron = [job.comment for job in cron]

    ### Take all UUID in database not ruuning or in error
    # Defne query
    uuid_sql = """ SELECT uuid FROM inputs
                   WHERE state!=100 OR
                         update < CURRENT_TIMESTAMP - interval '1 hour'; """
    # Connect to database
    cursor = connect_dbb()
    # Query dbb
    cursor.execute(uuid_sql)

    ### Launch all new inputs
    for uuid in cursor.fetchall():
        # Check if new input
        if not uuid[0] in l_cron:
            job = cron.new(command=sys.executable + ' ' + __file__ +\
                                   ' ' + uuid[0],
                           comment=uuid[0])
            job.minute.every(MAX_TIME_PROCESS)
            cron.write()
            time.sleep(DELAY_BETWEEN_PROCESS)

def temp_launcher():
    """
    launch all  process cab in different directory

    Returns
    -------
    None.

    """

    ### Take all UUID in database not ruuning or in error
    # Defne query
    uuid_sql = """ SELECT uuid FROM inputs
                   WHERE state!=100 OR
                         update < CURRENT_TIMESTAMP - interval '1 hour'; """
    # Connect to database
    cursor = connect_dbb()
    # Query dbb
    cursor.execute(uuid_sql)

    ### Launch all new inputs
    for uuid in cursor.fetchall():
        subprocess.call([sys.executable , __file__ , uuid[0]])
        time.sleep(DELAY_BETWEEN_PROCESS)

def temp_background(uuid):
    """


    Parameters
    ----------
    uuid : TYPE
        DESCRIPTION.

    Returns
    -------
    None.

    """
    # Wait have CPU and RAM to process
    while True:
        if not (psutil.cpu_percent(1) < 90 and
               psutil.virtual_memory().available > SIZE_PROCESS):
            continue

        # unzip
        unzip(uuid)

        # Connect of database
        cursor = connect_dbb()

        # Query to update database when processed image
        pi_sql = """UPDATE inputs SET state=%(state)s, update=CURRENT_TIMESTAMP
                    WHERE uuid=%(uuid)s;"""

        # Query get option
        option_sql = """ SELECT options FROM inputs WHERE uuid=%(uuid)s;"""

        ### Run Cab
        # Get binary of cab
        cab_bin = os.path.join(os.path.dirname(sys.executable), 'cab')
        # Define path of directory with input images
        path_in = os.path.join(os.path.dirname(__file__), 'temp', uuid,
                               'extract')
        # Define path where save result of cab
        path_out = os.path.join(os.path.dirname(__file__), 'temp',
                                uuid + '_temp')

        # Define option of cab
        cursor.execute(option_sql, {'uuid':uuid})
        options = ' -l -i ' + path_in + ' -o ' + path_out + ' ' + \
                  cursor.fetchone()[0]
        # launch cab
        os.system(cab_bin + options)

        ### TODO update status of cab
        cursor.execute(pi_sql, {'state':100, 'uuid':uuid})

        ### Zip result
        # Define option for command lin zipfile
        sys.argv[1] = '-c ' + os.path.join(os.path.dirname(__file__), 'temp',
                                           uuid) + '.zip ' + path_out
        sys.argv[1:] = sys.argv[1].split()
        # Run function zip of zipfile
        runpy.run_module('zipfile', run_name="__main__")
        ### Notify by user of end process
        ## Get email of owner
        # Define query
        email_sql = """ SELECT email FROM my_user
                        WHERE login=(SELECT login FROM inputs
                                     WHERE uuid=%(uuid)s);
                    """
        # Query database
        cursor.execute(email_sql, {'uuid':uuid})

        send_email(dst=cursor.fetchone()[0],sub=_('msg_email_sub_end_cab'),
                   msg=_('msg_email_header_end_cab') + '\r\n\r\n' + uuid +
                       '\r\n\r\n' + _('msg_email_end'))

        break

if __name__ == "__main__":
    if len(sys.argv) == 2:
        temp_background(sys.argv[1])
