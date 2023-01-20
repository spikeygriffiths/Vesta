#!sendmail.py

import yagmail
# Application-specific modules
import config
import log

def email(subject, text, html):
    smtpUser = config.Get("smtpUser")
    smtpPass = config.Get("smtpPass")
    addrTo = config.Get("emailAddress")
    appTitle = config.Get("appTitle", "Vesta")
    if smtpUser != None and smtpPass != None and addrTo != None:
        try:
            yag = yagmail.SMTP(user=smtpUser, password=smtpPass)
            yag.send(to=addrTo, subject=appTitle, contents=text)
            log.debug("Email sent successfully")
        except Exception as e:
            log.fault("Email:Failed to send with exception Code: {c}, Message, {m}".format(c = type(e).__name__, m = str(e)))
    else:
        log.fault("Email:Need smtpUser, smtpPass and emailAddress in database")
