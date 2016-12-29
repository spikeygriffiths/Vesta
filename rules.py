#!rules.py

import events
import log
import hubapp
import devices

if __name__ == "__main__":
    hubapp.main()

rules = []

def EventHandler(eventId, arg):
    if (eventId == events.ids.INIT):
        Read()  # Ought to load existing set of rules so we know how to respond to events
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
        Run("On_"+arg[1], devIndex) # Trigger is "On_xxxx" where xxxx is network Id for device

def Read()
    try:
        with open("rules.txt", "r") as f:
            try:
                rules = eval(f.read()) # Load previous cache of devices into info[]
                log.log("Got Rules")
            except:
                rules = []
                log.log("Bad Rules")
    except OSError:
        rules = []
        log.log("No Rules")

def Run(trigger, args): # Run through the rules looking to see if we have a handler for the trigger
    Read() # In case rules have changed since last time(?)
    for rule in rules:
        RunLine(rule, trigger, args)

def RunLine(rule, trigger, args):
    # Each rule consists of a trigger and an associated action to take if trigger matches, as a dictionary entry
    # CONTINUE HERE!


