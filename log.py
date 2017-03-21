#!log.py

from datetime import datetime
from subprocess import call
# App-specific Python modules
import devices

def Init(msg):
    try:
        log(msg)
    except:
        call("sudo rm hub.log", shell=True) # Remove unusable log if necessary (we may be recovering from a power cut in the middle of writing the log)
        
def log(msg):
    timedMsg = "<" + str(datetime.now()) + ">"+ msg
    print(timedMsg)  # To stdout.  Relies on stdout being re-directed to hub.log (so that it includes crash information)

def fault(msg):
    log("FAULT! " + msg)

def RollLogs():
    call("rm yesterday.log", shell=True) # Remove yesterday's old log
    call("mv hub.log yesterday.log", shell=True) # Move today's log to yesterday's, getting ready to start new log from now

