#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Nov  9 10:52:18 2022

@author: mpalerme


"""
import sys
sys.path.append(__file__)
from crontab import CronTab
import time
import sys
import connect as ct
import os
import psutil
from connect import connect_dbb
from zipfile import ZipFile as zf
import runpy


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
    zip_name = os.listdir(dir_zip)[0]

    # create extract directory
    os.makedirs(dir_extract)

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

        # Connect of database
        cursor = connect_dbb()

        # Query to update database when processed image
        pi_sql = """UPDATE inputs SET state=%(state)s, update=CURRENT_TIMESTAMP
                    WHERE uuid=%(uuid)s;"""

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
        options = ' -l -i ' + path_in + ' -o ' + path_out + ' -n 1 -c'
        # launch cab
        os.system(cab_bin + options)

        ### TODO update status of cab
        cursor.execute(pi_sql, {'state':100, 'uuid':uuid})

        ### Zip result
        # Define option for command lin zipfile
        sys.argv[1] = '-c ' + os.path.join(os.path.dirname(__file__), 'temp', uuid) + '.zip ' + path_out
        sys.argv[1:] = sys.argv[1].split()
        # Run function zip of zipfile
        runpy.run_module('zipfile', run_name="__main__")




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
    cursor = ct.connect_dbb()
    # Query dbb
    cursor.execute(uuid_sql)

    ### Launch all new inputs
    for uuid in cursor.fetchall():
        # Check if new input
        if not uuid[0] in l_cron:
            job = cron.new(command=sys.executable + ' ' + __file__ + ' ' + uuid[0],
                           comment=uuid[0])
            job.minute.every(MAX_TIME_PROCESS)
            cron.write()
            time.sleep(DELAY_BETWEEN_PROCESS)

if __name__ == "__main__":
    if len(sys.argv) == 2:
        background(sys.argv[1])
