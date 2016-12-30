#!rules.py

from datetime import datetime
from datetime import timedelta
# App-specific Python modules
import events
import log
import hubapp
import devices

if __name__ == "__main__":
    hubapp.main()

# Example rules.txt
# if HallwayPir==active do SwitchOn ["HallwayLight","120s"]
# if HallwayBtn==on do Toggle ["HallwayLight"]
# Later on might have:
# if HallwayPir==active do {
#   if time>sunset and time<=25:00 do SwitchOn ["HallwayLight","120s"]
#   if time>sunset and time<=20:00 do SwitchOn ["StairLight","120s"]
#   if time>20:00 and time<=25:00 do FadeOn ["StairLight","120s","25%"]
# }
# Note spaces used to separate each item.  Time wrapping around midnight is handled by adding 24, hence 25:00 being 1am
# Syntax is "if <condition> do <action>"

def EventHandler(eventId, arg):
    if eventId == events.ids.TRIGGER:
        devIdx = devices.GetIdx(arg[1]) # Lookup device from network address in arg[1]
        userName = devices.GetVal(devIdx, "UserName")
        devName = devices.GetAttrVal(devIdx, "0000", "0005") # Device name
        #devManuf = devices.GetAttrVal(devIdx, "0000", "0004") # Manufacturer name
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
        devIdx = devices.GetIdx(arg[1]) # Lookup device from network address in arg[1]
        userName = devices.GetVal(devIdx, "UserName")
        log.log("Button "+ arg[1]+ " "+arg[0]) # Arg[0] holds "On", "Off" or "Toggle"
        if userName:
            Run(userName+"==active", devIdx) # See if rule exists
    elif eventId == events.ids.SECONDS: # See if any devices are timing out, and turn them off if necessary
        for devIdx, devInfo in enumerate(devices.info): # Go through all devices
            offAt = devices.GetVal(devIdx, "SwitchOff@")
            if offAt:
                if datetime.now() >= offAt:
                    devices.SwitchOff(devIdx)

def Run(trigger, args): # Run through the rules looking to see if we have a handler for the trigger
    rules = open("rules.txt").readlines() # Load rules
    for line in range(len(rules)):
        rule = ' '.join(rules[line].split()) # Compact multiple spaces into single ones and make each line into a rule
        ruleList = rule.split(" ") # Make each rule into a list
        if ruleList[0] == "if":
            if ParseCondition(ruleList, 1): # Parse condition from element 1 
                index = 1
                for item in ruleList: # Look for "do" command
                    index = index + 1
                    if item == "do":
                        Action(ruleList, index)
            # else skip rest of line
        elif ruleList[0] == "do":
            Action(ruleList, 1)
        # else assume the line is a comment and skip it
    # end of rules

def ParseCondition(conditionList, index):
    return True

def Action(actList, index):
    args = eval(actList[index+1]) # Read args into list
    devIdx = devices.GetIdxFromUsername(args[0]) # First arg is username for device
    if devIdx != None:
        if actList[index] == "SwitchOn":
            devices.SwitchOn(devIdx,int(args[1],10)) # Duration in args[1]
        elif actList[index] == "SwitchOff":
            devices.SwitchOff(devIdx)
        elif actList[index] == "Toggle":
            devices.Toggle(devIdx)
        elif actList[index] == "FadeOn":
            devices.FadeOn(devIdx,int(args[1],10),int(args[2],10)) # Level (as percentage) in args[1], Duration in args[2]
        # add more actions here!
    else:
        log.fault("Device "+args[0]+" from rules.txt not found in devices")

