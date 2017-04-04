#!rules.py

from datetime import datetime
from datetime import timedelta
from pathlib import Path
from subprocess import call
# App-specific Python modules
import events
import log
import devices
import zcl
import variables
import iottime
import database
import config

rulesFilename = "rules.txt"

# Example rules.txt
# if HallwayPir==active do SwitchOn HallwayLight for 120
# if HallwayBtn==TOGGLE do Toggle HallwayLight
# if HallwayPir==active and 16:00<time<23:59 do SwitchOn HallwayLight for 120
# if HallwayPir==active and 0:00<time<1:00 do SwitchOn HallwayLight for 120
# if StairPir==active and 16:00<time<20:00 do SwitchOn StairLight for 120
# if StairPir==active and 20:00<time<23:00 do Dim StairLight to 0.15 for 120
#if DoorBell==TOGGLE and 7:00<time<20:59 do Play Westminster-chimes.mp3
#if DoorBell==TOGGLE and 21:00<time<23:59 do email Out of hours doorbell

# Note spaces used to separate each item.
# Syntax is "if <condition> do <action>[ for <duration in seconds>]"

def EventHandler(eventId, eventArg):
    if eventId == events.ids.TRIGGER:
        devIdx = devices.GetIdx(eventArg[1]) # Lookup device from network address in eventArg[1]
        now = datetime.now()
        nowStr = now.strftime("%H:%M")
        zoneType = database.GetDeviceItem(devIdx, "iasZoneType") # Device type
        if zoneType != None:
            oldState = database.GetLatestEvent(devIdx)
            if zoneType == zcl.Zone_Type.Contact:
                if int(eventArg[3], 16) & 1: # Bottom bit indicates alarm1
                    newState = "opened"
                else:
                    newState = "closed"
                if oldState != newState:    # NB Might get same state if sensor re-sends, or due to battery report 
                    database.NewEvent(devIdx, newState) # For web page.  Only update event log when state changes
                    DeviceRun(devIdx, "=="+newState) # See if rule exists (when state changes)
                    #log.debug("Door "+ eventArg[1]+ " "+newState)
            elif zoneType == zcl.Zone_Type.PIR:
                if int(eventArg[3], 16) & 1: # Bottom bit indicates alarm1
                    newState = "active"
                    devices.SetTempVal(devIdx, "PirInactive@", datetime.now()+timedelta(seconds=300))
                else:
                    newState = "inactive" # Might happen if we get an IAS battery report
                if oldState != newState:
                    database.NewEvent(devIdx, newState) # For web page.  Only update event log when state changes
                DeviceRun(devIdx, "=="+newState) # See if rule exists
            else:
                log.debug("DevId: "+ eventArg[1]+" zonestatus "+ eventArg[3])
        else:
            log.fault("Unknown IAS device type for devId "+eventArg[1])
    elif eventId == events.ids.BUTTON:
        devIdx = devices.GetIdx(eventArg[1]) # Lookup device from network address in eventArg[1]
        #log.debug("Button "+ eventArg[1]+ " "+eventArg[0]) # Arg[0] holds "ON", "OFF" or "TOGGLE" (Case might be wrong)
        database.NewEvent(devIdx, "pressed") # For web page
        DeviceRun(devIdx, "=="+eventArg[0]) # See if rule exists
    # End of EventHandler

def DeviceRun(devIdx, restOfRule): # Run rule for specified device
    userName = database.GetDeviceItem(devIdx, "userName")
    Run(userName+restOfRule)
    groupList = database.GetGroupsWithDev(devIdx)    # Check if device is in any groups and run appropriate rules for each group
    for name in groupList:
        Run(name+restOfRule)

def Run(trigger): # Run through the rules looking to see if we have a match for the trigger
    rulesFile = Path(rulesFilename)
    if rulesFile.is_file():
        call("sudo chmod 666 "+rulesFilename, shell=True)    # Make sure we can use it
        with open(rulesFilename) as rules:
            log.debug("Running rule: "+ trigger)
            if "==" in trigger:
                sep = trigger.index("==")
                triggerType = trigger[:sep]
                triggerVal = trigger[sep+2:]
                variables.Set(triggerType, triggerVal)
            for line in rules:
                rule = ' '.join(line.split()) # Compact multiple spaces into single ones and make each line into a rule
                ruleList = rule.split(" ") # Make each rule into a list
                if ruleList[0] == "if":
                    doIndex = FindItemInList("do", ruleList) # Safely look for "do"
                    if doIndex != None:
                        if ParseCondition(ruleList[1:doIndex], trigger) == True: # Parse condition from element 1 to "do" 
                            Action(ruleList[doIndex+1:]) # Do action
                    # else skip rest of line
                elif ruleList[0] == "do":
                    Action(ruleList[1:])
                # else assume the line is a comment and skip it
            # end of rules
            variables.Del(triggerType) # Make sure we don't re-run the same trigger
    else:
        call("touch "+rulesFilename, shell=True)
        log.fault("Made new " + rulesFilename+" !")

def FindItemInList(item, listToCheck):
    try:
        return listToCheck.index(item)
    except ValueError:
        return None

def ParseCondition(ruleConditionList, trigger):
    #log.debug("Parsing: "+" ".join(ruleConditionList))
    subAnswers = ""
    if ruleConditionList[0] == trigger: # If first condition (must be trigger) matches, then check rest
        #log.debug("condition: "+ruleConditionList[0]+ " = trigger: "+trigger)
        subAnswers = subAnswers + "True"
        if len(ruleConditionList) > 0: # Only parse rest of condition if first item is true
            for condition in ruleConditionList[1:]:
                if condition == "and":
                    subAnswers = subAnswers+" and " # Note surrounding spaces, for python eval()
                elif condition == "or":
                    subAnswers = subAnswers+" or "
                elif "<time<" in condition:
                    sep = condition.index("<time<") # Handle time here
                    nowTime = datetime.strptime(datetime.now().strftime("%H:%M"), "%H:%M")
                    startTime = iottime.Get(condition[:sep])
                    endTime = iottime.Get(condition[sep+6:])
                    if startTime <= nowTime <= endTime:
                       subAnswers = subAnswers + "True"
                    else:
                       subAnswers = subAnswers + "False"
                elif "<=" in condition:
                    subAnswers = subAnswers + str(GetConditionResult("<=", condition))
                elif ">=" in condition:
                    subAnswers = subAnswers + str(GetConditionResult(">=", condition))
                elif "<" in condition:
                    subAnswers = subAnswers + str(GetConditionResult("<", condition))
                elif ">" in condition:
                    subAnswers = subAnswers + str(GetConditionResult(">", condition))
                elif "==" in condition:
                    subAnswers = subAnswers + str(GetConditionResult("==", condition))
            # End of loop
    else: # Initial condition failed
        subAnswers = subAnswers + "False"
    if eval(subAnswers) == True:
        return True
    else:
        return False

def isNumber(s):
    try:
        float(s)
        return True
    except:
        return False

def GetConditionResult(test, condition):
    sep = condition.index(test) # Assume this has already been shown to return a valid answer
    varName = condition[:sep] # Variable must be on the left of the expression
    tstVal = condition[sep+len(test):] # Simple value must be on right
    varVal = variables.Get(varName)
    if varVal != None:
        if isNumber(tstVal):
            varVal = str(varVal)
            tstVal = str(tstVal)
        return eval(varVal + test + tstVal)
    else:
        return False # If we couldn't find the item requested, assume the condition fails(?)

def Action(actList):
    log.debug("Action with: "+str(actList))
    action = actList[0]
    if action == "Log":
        log.debug("Rule says Log event for "+' '.join(actList[1:]))
    elif action == "Play":
        filename = "Sfx/"+actList[1]
        call(["omxplayer", "-o", "local", filename])
    elif action == "Event":
        if actList[1] == "TimeOfDay":
            events.IssueEvent(events.ids.TIMEOFDAY, actList[2])
        elif actList[1] == "Alarm":
            events.IssueEvent(events.ids.ALARM, actList[2])
        # Could have other events here...
    elif action == "synopsis": # First arg is email recipient
        emailAddress = config.Get("emailAddress")
        if emailAddress != None:
            emailBody = []
            #for items in devices.synopsis:
            #    emailBody.append(' '.join(items))  # Tuples are joined by spaces
            #cmdList = ["echo", "\""+'\n'.join(emailBody)+"\"", "|", "mail", "-s", "\"Update from IoT-Hub\"", ]
            #cmdStr = " ".join(cmdList)
            #call(cmdStr, shell=True)
            #devices.synopsis = []   # Ready to start a new synopsis mail now
    elif action == "email": # All args are body of the text.  Fixed subject and email address
        emailAddress = config.Get("emailAddress")
        if emailAddress != None:
            emailBody = []
            for item in actList[1:]:
                emailBody.append(item)
            cmdList = ["echo", "\""+' '.join(emailBody)+"\"", "|", "mail", "-s", "\"Alert from IoT-Hub\"", emailAddress]
            cmdStr = " ".join(cmdList)
            call(cmdStr, shell=True)
    else: # Must be a command for a device, or group of devices
        name = actList[1]   # Second arg is name
        if database.IsGroupName(name): # Check if name is a groupName
            devIdxList = GetGroupDevs(name)
            for devIdx in devIdxList:
                CommandDev(action, devIdx, actList) # Command each device in list
        else:
            devIdx = database.GetDevIdx("userName", name)
            CommandDev(action, devIdx, actList) # Command one device

def CommandDev(action, devIdx, actList):
    if devIdx == None:
        log.fault("Device "+actList[1]+" from rules.txt not found in devices")
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
        elif action == "HueSat":    # Syntax is "do HueSat <Hue in degrees>,<fractional saturation>
            devices.Colour(devIdx, int(actList[3],10), float(actList[4]))
        else:
            log.debug("Unknown action: "+action +" for device: "+actList[1])

def SetOnDuration(devIdx, durationS):
    if durationS>0: # Duration of 0 means "Stay on forever"
        log.debug("Switching off after "+str(durationS))
        devices.SetTempVal(devIdx, "SwitchOff@", datetime.now()+timedelta(seconds=durationS))

