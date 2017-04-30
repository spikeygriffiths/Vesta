#!log.py

from datetime import datetime
from subprocess import call
# App-specific Python modules

def Init(msg):
    try:
        debug(msg)
    except:
        call("sudo rm hub.log", shell=True) # Remove unusable log if necessary (we may be recovering from a power cut in the middle of writing the log)
        
def debug(msg):
    timedMsg = "<" + str(datetime.now()) + ">"+ msg
    print(timedMsg)  # To stdout.  Relies on stdout being re-directed to hub.log (so that it includes crash information)

def fault(msg):
    debug("FAULT! " + msg)

def RollLogs(): # Called once/day
    call("sudo chmod 666 yesterday.log", shell=True)    # Make sure we can erase the old log
    call("rm yesterday.log", shell=True) # Remove yesterday's old log
    call("mv hub.log yesterday.log", shell=True) # Move today's log to yesterday's, getting ready to start new log from now

