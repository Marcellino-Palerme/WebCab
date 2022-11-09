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


MAX_TIME_PROCESS = 10
DELAY_BETWEEN_PROCESS = 1


def background(uuid):
    """


    Parameters
    ----------
    uuid : TYPE
        DESCRIPTION.

    Returns
    -------
    None.

    """
    with open(os.path.join(os.path.dirname(__file__), 'avoit.txt'), "a") as t_f:
        print(time.asctime( time.localtime(time.time()) ), file=t_f)
        print(str(uuid), file=t_f)


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
            job = cron.new(command=sys.executable + ' ' + __file__ + ' ' + uuid[0])
            job.minute.every(MAX_TIME_PROCESS)
            cron.write()
            time.sleep(DELAY_BETWEEN_PROCESS)

if __name__ == "__main__":
    if len(sys.argv) == 2:
        background(sys.argv[1])
