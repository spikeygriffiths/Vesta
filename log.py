#!log.py

from datetime import datetime
from subprocess import call
import os
# App-specific Python modules

def Init(msg):
    try:
        debug(msg)
    except:
        os.remove("today.log") # Remove unusable log if necessary (we may be recovering from a power cut in the middle of writing the log?)
    oldErr = "olderr.log"
    if os.path.isfile(oldErr):
        if os.path.getsize(oldErr) > 0:
            os.rename(oldErr, str(datetime.now())+"_err.log")    # If there's an "olderr.log" file, prepend the time (to ensure it won't overwrite any others) and continue
        else:
            os.remove(oldErr)   # Just delete any empty error log file, since it just means the last run didn't generate any errors
        
def debug(msg):
    log("debug:" + msg)
    
def fault(msg):
    log("FAULT:" + msg)

def log(msg):
    timedMsg = "<" + str(datetime.now()) + ">"+ msg
    open("today.log", "a").write(timedMsg+"\n")
    print(timedMsg)

def RollLogs(): # Called once/day
    os.replace("today.log","yesterday.log")

