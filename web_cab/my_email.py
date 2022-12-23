#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Oct 27 15:49:54 2022

@author: mpalerme
"""
import os
import smtplib, ssl
import json

def send_email(dst, sub, msg):
    """
    send email

    Parameters
    ----------
    dst : str
        email of addressee.
    sub : str
        email's subject.
    msg : str
        content of email.

    Returns
    -------
    None.

    """
    # Get configurations
    with open(os.path.join(os.path.dirname(__file__),'conf','conf.json'),
              'r', encoding='utf-8') as f_conf:
        d_conf = json.load(f_conf)

    # Create message
    message = ("From: %s\r\nTo: %s\r\nSubject: %s\r\n\r\n%s" % ("Web Cab",
                                                                dst,
                                                                sub,
                                                                msg.encode('utf-8')))
    # Create a secure SSL context
    context = ssl.create_default_context()

    # Try to log in to server and send email
    try:
        server = smtplib.SMTP(d_conf['smtp_server'],587)
        server.ehlo() # Can be omitted
        server.starttls(context=context) # Secure the connection
        server.ehlo() # Can be omitted
        server.login(d_conf['sender_email'], d_conf['pwd_email'])
        server.sendmail(d_conf['sender_email'], dst, message)

    except Exception as e:
        # Print any error messages to stdout
        print(e)
    finally:
        server.quit()
    with open(os.path.join(os.path.dirname(__file__), 'pwd.txt'), 'w') as fp:
        print(msg, file=fp)

send_email('mpalerme@inrae.fr', 'coucou', 'rien')
