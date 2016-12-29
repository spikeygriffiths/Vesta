#!rules.py

import events
import log
import hubapp
import devices

if __name__ == "__main__":
    hubapp.main()

def EventHandler(eventId, arg):
    #if (eventId == ids.INIT):
    # Ought to load existing set of rules so we know how to respond to events
    if eventId == events.ids.TRIGGER:
        devIndex = devices.GetIdx(arg[1]) # Lookup device from network address in arg[1]
        devName = devices.GetAttrVal(devIndex, "0000", "0005") # Device name
        #devManuf = devices.GetAttrVal(devIndex, "0000", "0004") # Manufacturer name
        if devName != None:
            #log.log("DevId: "+arg[1]+" has name "+ devName)
            if devName == "DWS003":
                if int(arg[3], 16) & 1: # Bottom bit indicates alarm1
                    log.log("Door "+ arg[1]+ " opened")
                else:
                    log.log("Door "+ arg[1]+ " closed")
            elif devName == "MOT003":
                log.log("PIR ", arg[1]+ " active")
            else:
                log.log("DevId: "+ arg[1]+" zonestatus "+ arg[3])
    elif eventId == events.ids.BUTTON:
        devIndex = devices.GetIdx(arg[1]) # Lookup device from network address in arg[1]
        log.log("Button "+ arg[1]+ " "+arg[0]) # Arg[0] holds "On", "Off" or "Toggle"
