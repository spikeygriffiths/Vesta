#!/usr/bin/env python3 
# hubapp.py
# For Raspberry Pi using Telegesis USB stick to talk to array of ZigBee devices

import time
# App-specific Python modules
import events
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
        log.debug("   *** Starting hubapp, v0.1.0.0 ***")
        log.debug("   *********************************")
    # end event handler

if __name__ == "__main__":
    main()

