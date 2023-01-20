#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Nov  9 10:52:18 2022

@author: mpalerme


"""
import zipfile
from zipfile import ZipFile as zf
import time
import os
import sys
import psutil
import shutil

import threading as th

sys.path.append(os.path.dirname(__file__))
from connect import connect_dbb
from my_email import send_email
from translate import _

# % used by one CAB runnning
CPU = 2
# % used by all process
g_cpu_used = 0
# size RAM used by one CAB running
RAM = 50 * 1024 * 1024 # 50 MB
# size RAM used by all process
g_ram_used = 0

sem = th.Semaphore()

def available_ressources():
    """
    Indicate if stay ressources to run CAB

    Returns
    -------
    bool.

    """
    sem.acquire()
    # Verify we not up to 90% of cpu
    b_return = 90 > (psutil.cpu_percent(1) + g_cpu_used + CPU)
    # Verify stay 10 MB of RAM
    b_return &= 10 * 1024 * 1024 < (psutil.virtual_memory().available -
                                    g_ram_used - RAM)
    sem.release()

    return b_return


def unzip(uuid, path_temp):
    """
    unzip

    Parameters
    ----------
    path_temp : str
        path where save inputs.
    uuid : str
        name of directory with zip.

    Returns
    -------
    None.

    """
    # Define path of directory contain zip
    dir_zip = os.path.join(path_temp, uuid)
    # Define path where extract zip
    dir_extract = os.path.join(path_temp, uuid, 'extract')

    # Take name of zip
    zip_name = list(filter(lambda l_f: 'zip' in l_f, os.listdir(dir_zip)))[0]

    if not zipfile.is_zipfile(os.path.join(dir_zip, zip_name)):
        return False

    # create extract directory
    os.makedirs(dir_extract, exist_ok=True)

    # Open Zip
    try:
        zip_f = zf(os.path.join(dir_zip, zip_name),'r')

    except zipfile.BadZipfile:
        print('erreur zip')
        return False

    # Check image not upper 20Mb
    for zp_info in zip_f.filelist:
        if zp_info.file_size > 20 * 1024 *1024:
            return False

    # Extract zip
    zip_f.extractall(path=dir_extract)

    return True



def delete_input(uuid, path_temp):
    """
    delete the input

    Parameters
    ----------
    uuid : str
        Id of process.

    path_temp : str
        Where save inputs

    Returns
    -------
    None.

    """
    shutil.rmtree(os.path.join(path_temp, uuid))
    shutil.rmtree(os.path.join(path_temp, uuid + '_temp'))

def end_process(uuid, path_temp):
    """
    end part of processing image

    Parameters
    ----------
    uuid : str
        name of directory with zip.
    path_temp : str
        path where save inputs.

    Returns
    -------
    None.

    """
    global g_ram_used
    global g_cpu_used

    # Connect of database
    cursor = connect_dbb()

    # Query to update database when processed image
    pi_sql = """UPDATE inputs SET state=%(state)s, update=CURRENT_TIMESTAMP
                WHERE uuid=%(uuid)s;"""

    # Define path where save result of cab
    path_out = os.path.join(path_temp, uuid + '_temp')

    ### Zip result
    os.system(sys.executable + ' -m zipfile -c ' + os.path.join(path_temp,
                                                                uuid)
              + '.zip ' + path_out)
    # # Define option for command lin zipfile
    # sys.argv[1] =
    # sys.argv[1:] = sys.argv[1].split()
    # # Run function zip of zipfile
    # runpy.run_module('zipfile', run_name="__main__")

    # Indicate end of process
    cursor.execute(pi_sql, {'state':100, 'uuid':uuid})

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

    # Delete Inputs
    delete_input(uuid, path_temp)

    # Release ressources
    sem.acquire()
    g_ram_used -= RAM
    g_cpu_used -= CPU
    sem.release()


def background(uuid, path_temp):
    """
    processing image with cab

    Parameters
    ----------
    uuid : str
        name of directory with zip.
    path_temp : str
        path where save inputs.

    Returns
    -------
    None.

    """
    global g_ram_used
    global g_cpu_used

    # Verify stay CPU and RAM to process
    if (available_ressources() is False):
        exit(1)

    # Acquire ressources
    sem.acquire()
    g_ram_used += RAM
    g_cpu_used += CPU
    sem.release()

    # Define path where save result of cab
    path_out = os.path.join(path_temp, uuid + '_temp')

    # unzip
    if not unzip(uuid, path_temp):
        with open(os.path.join(path_out, 'error.txt'), 'w') as err_f:
            print(_('msg_error_zip'),file=err_f)
        end_process(uuid, path_temp)
        return 5

    # Connect of database
    cursor = connect_dbb()

    # Query to update database when processed image
    pi_sql = """UPDATE inputs SET state=%(state)s, update=CURRENT_TIMESTAMP
                WHERE uuid=%(uuid)s;"""

    # Query get option
    option_sql = """ SELECT options FROM inputs WHERE uuid=%(uuid)s;"""

    # Indicate we started process
    cursor.execute(pi_sql, {'state':0, 'uuid':uuid})

    ### Run Cab
    # Get binary of cab
    cab_bin = os.path.join(os.path.dirname(sys.executable), 'cab')
    # Define path of directory with input images
    path_in = os.path.join(path_temp, uuid,
                           'extract')


    # Define option of cab
    cursor.execute(option_sql, {'uuid':uuid})
    options = ' -l -i ' + path_in + ' -o ' + path_out + ' ' + \
              cursor.fetchone()[0]
    # launch cab
    os.system(cab_bin + options)

    end_process(uuid, path_temp)

    return 0




def launcher(path_temp):
    """
    launch all cron to process cab in different directory

    Parameters
    ----------

    path_temp : str
        path where save inputs.

    Returns
    -------
    None.

    """

    ### Take all UUID in database not ruuning or in error
    # Defne query
    uuid_sql = """ SELECT uuid FROM inputs
                   WHERE state!=100 AND
                         (update < CURRENT_TIMESTAMP - interval '1 hour' OR
                          update IS NULL); """
    # Connect to database
    cursor = connect_dbb()

    # Query dbb
    cursor.execute(uuid_sql)

    ### Launch all new inputs
    for uuid in cursor.fetchall():
        my_thread = th.Thread(target=background, args=(uuid[0], path_temp))
        my_thread.start()


def delete(path_temp):
    """
    delete all expired done process

    Parameters
    ----------
    path_temp : TYPE
        DESCRIPTION.

    Returns
    -------
    None.

    """
    ### Take all UUID in database done and expired
    # Defne query
    uuid_sql = """ SELECT uuid FROM inputs
                   WHERE state=100 AND
                         update + interval ' 2 days'< CURRENT_TIMESTAMP ;
               """
    # Connect to database
    cursor = connect_dbb()

    # Query dbb
    cursor.execute(uuid_sql)

    ### Delete process
    for uuid in cursor.fetchall():
        ## In Database
        # Define query
        delete_sql = """ DELETE FROM inputs WHERE uuid=%(uuid)s;"""

        # Query database
        cursor.execute(delete_sql, {'uuid':uuid[0]})

        # On disk
        os.remove(os.path.join(path_temp, uuid[0] + '.zip'))

def scheduler(path_temp):
    """


    Parameters
    ----------
    path_temp : TYPE
        DESCRIPTION.

    Returns
    -------
    None.

    """

    watch = 0
    while(True):
        watch += 1

        # Every one minute we check if we need launch processes
        th.Thread(target=launcher, args=(path_temp,)).start()

        # Every 2 hours we check if we can delete Done process
        if watch > 120:
            delete(path_temp)
            watch = 0

        # Wait 1 minutes
        time.sleep(60)




if __name__ == "__main__":
    print(sys.argv)
    path_temp = os.path.join(os.path.dirname(__file__), 'temp')
    # my_thread = th.Thread(target=launcher, args=(path_temp,))
    # my_thread.start()
    scheduler(path_temp)
