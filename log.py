#!log.py

from datetime import datetime
from subprocess import call
# App-specific Python modules
import devices

def Init(msg):
    try:
        log(msg)
    except:
        call("sudo rm debug.log", shell=True) # Remove unusable log if necessary (we may be recovering from a power cut in the middle of writing the log)
        
def log(msg):
    timedMsg = "<" + str(datetime.now()) + ">"+ msg
    open("debug.log", "a").write(timedMsg+"\n")
    print(timedMsg)  # To stdout

def fault(msg):
    timedMsg = "<" + str(datetime.now()) + ">"+ msg
    open("fault.log", "a").write(timedMsg+"\n")
    print("FAULT! "+ msg)  # To stdout

def activity(devIdx, value):
    if devIdx=="hub":
        username = "Hub"
    else:
        username = devices.GetUserNameFromDevIdx(devIdx)
    open("activity.log", "a").write(username+" "+value+" @ "+str(datetime.now())+"\n")

def NewLog():
    call("rm old_debug.log", shell=True) # Remove yesterday's old log
    call("mv debug.log old_debug.log", shell=True) # Move today's log to yesterday's, getting ready to start new log from now

