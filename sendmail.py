#!sendmail.py

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
# Application-specific modules
import config
import log

def email(subject, text, html):
    smtpServer = config.Get("smtpServer")
    smtpPort = int(config.Get("smtpPort"))
    smtpUser = config.Get("smtpUser")
    smtpPass = config.Get("smtpPass")
    addrTo = config.Get("emailAddress")
    appTitle = config.Get("appTitle", "Vesta")
    if smtpServer != None and smtpUser != None and smtpPass != None and addrTo != None:
        addrFrom = appTitle + "<" + smtpUser + ">"
        if html != None:
            msg = MIMEMultipart('alternative')
            # Record the MIME types of both parts - text/plain and text/html
            part1 = MIMEText(text, 'plain')
            msg.attach(part1)
            part2 = MIMEText(html, 'html')
            msg.attach(part2)
        else: # No HTML
            msg = MIMEText(text)
        msg['To'] = addrTo
        msg['From'] = addrFrom
        msg['Subject'] = subject
        # Send the message via an SMTP server
        try:
            s = smtplib.SMTP_SSL(smtpServer, smtpPort)
            s.ehlo()
            s.login(smtpUser, smtpPass)
            s.sendmail(addrFrom, addrTo, msg.as_string())
            s.close()
            #s.quit()
        except Exception as e:
            log.fault("SMTP:Failed to send with exception Code: {c}, Message, {m}".format(c = type(e).__name__, m = str(e)))
            log.debug("SMTP:Sending to:" + addrTo + ", from:" + addrFrom)
            log.debug("SMTP:Server:" + smtpServer + ", port:" + str(smtpPort))
            log.debug("SMTP:User:" + smtpUser + ", smtpPass:" + smtpPass)
            if html != None:
                log.debug("SMTP:HTML:" + html)
            log.debug("SMTP:Text:" + text)
    else:
        log.fault("SMTP:Need smtpUser, smtpPass, smtpServer and emailAddress in config.txt")
