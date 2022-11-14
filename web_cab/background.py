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
import re
from zipfile import ZipFile as zf


MAX_TIME_PROCESS = 10
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

    dir_extract = os.path.join(path_temp, uuid)

    zip_name = os.listdir(dir_extract)[0]

    # Open Zip
    with zf(os.path.join(dir_extract, zip_name),'r') as zip_f:
        # Extract zip
        for index, name_file in enumerate(zip_f.namelist()):
            os.makedirs(os.path.join(dir_extract, str(index)))
            os.makedirs(os.path.join(dir_extract + '_temp', str(index)))
            zip_f.extract(name_file,
                          path=os.path.join(dir_extract, str(index)))
            rn_name_file = re.sub('[^\.a-zA-Z0-9]', '_', name_file)
            # rename extract file
            os.rename(os.path.join(dir_extract, str(index), name_file),
                      os.path.join(dir_extract, str(index), rn_name_file))


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

        ### Get status of uuid
        uuid_sql = """ SELECT total_file, state FROM inputs WHERE uuid=%(uuid)s;
                   """
        # Query ddatabase
        cursor.execute(uuid_sql, {'uuid':uuid})

        info_uuid = cursor.fetchone()

        # Unzip  if first time we process zip
        if info_uuid[1]==0:
            unzip(uuid)

        # Query to update database when processed image
        pi_sql = """UPDATE inputs SET state=%(state)s, update=CURRENT_TIMESTAMP
                    WHERE uuid=%(uuid)s;"""

        for index in range(info_uuid[1], info_uuid[0]):
            cab_bin = os.path.join(os.path.dirname(sys.executable), 'cab')
            path_in = os.path.join(os.path.dirname(__file__), 'temp', uuid,
                                   str(index))
            path_out = os.path.join(os.path.dirname(__file__), 'temp',
                                    uuid + '_temp', str(index))
            options = ' -l -i ' + path_in + ' -o ' + path_out + ' -n 1 -c'
            os.system(cab_bin + options)
            cursor.execute(pi_sql, {'state':index + 1, 'uuid':uuid})



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

    ### Take all UUID in database
    # Defne query
    uuid_sql = """ SELECT uuid FROM inputs; """
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
