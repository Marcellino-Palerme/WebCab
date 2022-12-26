#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Oct 27 15:49:54 2022

@author: mpalerme
"""
import os
import smtplib, ssl
from email.message import EmailMessage
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
    message = EmailMessage()
    message.set_content(msg)
    message['From'] = d_conf['sender_email']
    message['To'] = dst
    message['Subject'] = sub

    # Create a secure SSL context
    context = ssl.create_default_context()

    # Try to log in to server and send email
    try:
        server = smtplib.SMTP(d_conf['smtp_server'],587)
        server.starttls(context=context) # Secure the connection
        server.login(d_conf['sender_email'], d_conf['pwd_email'])
        server.send_message(message)

    except Exception as e:
        # Print any error messages to stdout
        with open('email.log', 'a') as f_mail:
            print(e, file=f_mail)
    finally:
        server.quit()
