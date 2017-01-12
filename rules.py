#!rules.py

from datetime import datetime
from datetime import timedelta
from pathlib import Path
# App-specific Python modules
import events
import log
import hubapp
import devices
import zcl

if __name__ == "__main__":
    hubapp.main()

rulesFilename = "rules.txt"

# Example rules.txt
# if HallwayPir==active do SwitchOn HallwayLight for 120
# if HallwayBtn==TOGGLE do Toggle HallwayLight
# Later on might have:
# if HallwayPir==active and 16:00 < time < 25:00 do SwitchOn HallwayLight for 120
# if StairPir==active and 16:00 < time < 20:00 do SwitchOn StairLight for 120
# if StairPir==active and 20:00 < time < 25:00 do Dim StairLight to 0.15 for 120

# Note spaces used to separate each item.  Time wrapping around midnight is handled by adding 24, hence 25:00 being 1am
# Syntax is "if <condition> do <action>[ for <duration>]"

def EventHandler(eventId, eventArg):
    if eventId == events.ids.TRIGGER:
        devIdx = devices.GetIdx(eventArg[1]) # Lookup device from network address in eventArg[1]
        userName = devices.GetVal(devIdx, "UserName")
        zoneType = devices.GetAttrVal(devIdx, zcl.Cluster.IAS_Zone, zcl.Attribute.Zone_Type) # Device type
        if zoneType != None:
            #log.log("DevId: "+arg[1]+" has type "+ zoneType)
            if zoneType == zcl.Zone_Type.Contact:
                if int(arg[3], 16) & 1: # Bottom bit indicates alarm1
                    log.log("Door "+ eventArg[1]+ " opened")
                else:
                    log.log("Door "+ eventArg[1]+ " closed")
            elif zoneType == zcl.Zone_Type.PIR:
                if userName:
                    Run(userName+"==active", devIdx) # See if rule exists
                else:
                    log.log("PIR "+ eventArg[1]+ " active")
            else:
                log.log("DevId: "+ eventArg[1]+" zonestatus "+ eventArg[3])
        else:
            log.fault("Unknown IAS device type for devId "+eventArg[1])
    elif eventId == events.ids.BUTTON:
        devIdx = devices.GetIdx(eventArg[1]) # Lookup device from network address in eventArg[1]
        userName = devices.GetVal(devIdx, "UserName")
        log.log("Button "+ eventArg[1]+ " "+eventArg[0]) # Arg[0] holds "ON", "OFF" or "TOGGLE" (Case might be wrong)
        if userName:
            Run(userName+"=="+eventArg[0], devIdx) # See if rule exists
    elif eventId == events.ids.SECONDS: # See if any devices are timing out, and turn them off if necessary
        for devIdx, devInfo in enumerate(devices.info): # Go through all devices
            offAt = devices.GetVal(devIdx, "SwitchOff@")
            if offAt:
                if datetime.now() >= offAt:
                    devices.SwitchOff(devIdx)

def Run(trigger, devIdx): # Run through the rules looking to see if we have a match for the trigger
    log.log("Running rule: "+ trigger)
    rulesFile = Path(rulesFilename)
    if rulesFile.is_file():
        with open(rulesFilename) as rules:
            for line in rules:
                rule = ' '.join(line.split()) # Compact multiple spaces into single ones and make each line into a rule
                ruleList = rule.split(" ") # Make each rule into a list
                if ruleList[0] == "if" and ruleList[2] == "do":
                    if ParseCondition(ruleList[1], trigger) == True: # Parse condition from element 1 
                        Action(ruleList[3:]) # Do action from element 3 onwards
                    # else skip rest of line
                elif ruleList[0] == "do":
                    Action(ruleList[1:])
                # else assume the line is a comment and skip it
            # end of rules
    else:
        log.fault("No " + rulesFilename+" !")

def ParseCondition(ruleCondition, trigger):
    if ruleCondition == trigger: # Simple match for now
        return True
    else:
        return False

def Action(actList):
    log.log("Action with: "+str(actList))
    action = actList[0]
    if action == "Log":
        log.log("Rule says Log event for "+actList[1])
    else:
        devIdx = devices.GetIdxFromUserName(actList[1]) # Second arg is username for device
        if devIdx == None:
            log.fault("Device "+actList[0]+" from rules.txt not found in devices")
        else:
            if action == "SwitchOn":
                devices.SwitchOn(devIdx)
                if len(actList) > 3:
                    if actList[2] == "for":
                        SetOnDuration(devIdx, int(actList[3],10))
            elif action == "SwitchOff":
                devices.SwitchOff(devIdx)
            elif action == "Toggle":
                devices.Toggle(devIdx)
            elif action == "Dim" and actList[2] == "to":
                devices.Dim(devIdx,float(actList[3]))
                if len(actList) > 5:
                    if actList[4] == "for":
                        SetOnDuration(devIdx, int(actList[5],10))
            else:
                log.log("Unknown action: "+action +" for device: "+devices.GetUserName(devIdx))

def SetOnDuration(devIdx, durationS):
    if durationS>0: # Duration of 0 means "Stay on forever"
        log.log("Switching off after "+str(durationS))
        devices.SetTempVal(devIdx, "SwitchOff@", datetime.now()+timedelta(seconds=durationS))

