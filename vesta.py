#!/usr/bin/env python3 
# vesta.py
# (Vesta was the Roman goddess of hearth and home, hence the fire logo.)
# For Raspberry Pi using Telegesis USB stick to talk to array of ZigBee HA devices

import time
import os
import sys
# App-specific Python modules
import events
import database
import log

def main():
    events.Issue(events.ids.PREINIT)
    events.Issue(events.ids.INIT)
    sleepDelayS = 0.1
    while True:
        time.sleep(sleepDelayS)
        events.Issue(events.ids.SECONDS, sleepDelayS)
    # end mainloop
     
def EventHandler(eventId, eventArg):
    if eventId == events.ids.INIT:
        log.Init     ("   *********************************")
        log.debug("   *** Starting Vesta, v" +GetVersion() + " ***", )
        log.debug("   *********************************")
    # end event handler

if __name__ == "__main__":
    main()

def GetVersion():
    return "1.0.0.7"

def Reboot():
    database.NewEvent(0, "Rebooting...") # 0 is always hub
    events.Issue(events.ids.SHUTDOWN)   # Tell system we're about to shutdown
    os.system("sudo reboot")    # Unrecoverable, so reboot entire machine...

def Restart():
    database.NewEvent(0, "Restarting...") # 0 is always hub
    events.Issue(events.ids.SHUTDOWN)   # Tell system we're about to shutdown
    sys.exit(0) # Stop app, and rely on cron job to restart us

