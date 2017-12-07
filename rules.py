#!rules.py

from datetime import datetime
from datetime import timedelta
from pathlib import Path
from subprocess import call
# App-specific Python modules
import events
import log
import devices
import devcmds
import zcl
import variables
import iottime
import database
import config
import telegesis
import status
import sendmail

# Example rules
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
        devKey = devices.GetKey(eventArg[1]) # Lookup device from network address in eventArg[1]
        if devKey != None:
            devices.NoteMsgDetails(devKey, eventArg)    # Note presence
            now = datetime.now()
            nowStr = now.strftime("%H:%M")
            zoneType = database.GetDeviceItem(devKey, "iasZoneType") # Device type
            if zoneType != None:
                oldState = database.GetLatestEvent(devKey)
                if zoneType == zcl.Zone_Type.Contact:
                    if int(eventArg[3], 16) & 1: # Bottom bit indicates alarm1
                        newState = "opened"
                    else:
                        newState = "closed"
                    if oldState != newState:    # NB Might get same state if sensor re-sends, or due to battery report 
                        database.NewEvent(devKey, newState) # For web page.  Only update event log when state changes
                        DeviceRun(devKey, "=="+newState) # See if rule exists (when state changes)
                        #log.debug("Door "+ eventArg[1]+ " "+newState)
                elif zoneType == zcl.Zone_Type.PIR:
                    if int(eventArg[3], 16) & 1: # Bottom bit indicates alarm1
                        newState = "active"
                        devices.SetTempVal(devKey, "PirInactive@", datetime.now()+timedelta(seconds=300))
                    else:
                        newState = "inactive" # Might happen if we get an IAS battery report
                    if oldState != newState:
                        database.NewEvent(devKey, newState) # For web page.  Only update event log when state changes
                    DeviceRun(devKey, "=="+newState) # See if rule exists
                else:
                    log.debug("DevId: "+ eventArg[1]+" zonestatus "+ eventArg[3])
            else:
                log.fault("Unknown IAS device type for devId "+eventArg[1])
        else: # devKey == None
            telegesis.Leave(eventArg[1])    # Tell device to leave the network, since we don't know anything about it
    elif eventId == events.ids.BUTTON:
        devKey = devices.GetKey(eventArg[1]) # Lookup device from network address in eventArg[1]
        if devKey != None:
            #log.debug("Button "+ eventArg[1]+ " "+eventArg[0]) # Arg[0] holds "ON", "OFF" or "TOGGLE" (Case might be wrong)
            database.NewEvent(devKey, "pressed") # For web page
            DeviceRun(devKey, "=="+eventArg[0]) # See if rule exists
        else: # devKey == None
            telegesis.Leave(eventArg[1])    # Tell device to leave the network, since we don't know anything about it
    # End of EventHandler

def DeviceRun(devKey, restOfRule): # Run rule for specified device
    userName = database.GetDeviceItem(devKey, "userName")
    Run(userName+restOfRule)
    groupList = database.GetGroupsWithDev(devKey)    # Check if device is in any groups and run appropriate rules for each group
    for name in groupList:
        Run(name+restOfRule)

def Run(trigger): # Run through the rules looking to see if we have a match for the trigger
    rules = database.GetRules(trigger)  # Get a list of all rules that mention trigger
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
                if ParseCondition(ruleList[1:doIndex], trigger) == True: # Parse condition from element 1 (ie immediately after "if") to "do" 
                    Action(ruleList[doIndex+1:]) # Do action
            # else skip rest of line
        elif ruleList[0] == "do":
            Action(ruleList[1:])
        # else assume the line is a comment and skip it
    # end of rules
    variables.Del(triggerType) # Make sure we don't re-run the same trigger

def FindItemInList(item, listToCheck):
    try:
        return listToCheck.index(item)
    except ValueError:
        return None

def ParseCondition(ruleConditionList, trigger):
    #log.debug("Parsing: "+" ".join(ruleConditionList))
    subAnswers = "True"
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
            if endTime < startTime: # Handle midnight-crossing here...
                almostMidnight = datetime.strptime("23:59", "%H:%M")
                midnight = datetime.strptime("0:00", "%H:%M")
                if nowTime > datetime.strptime("12:00", "%H:%M"): # After midday but before midnight
                   subAnswers = subAnswers + str(iottime.IsTimeBetween(startTime, nowTime, almostMidnight))
                else: # Assume after midnight
                   subAnswers = subAnswers + str(iottime.IsTimeBetween(midnight, nowTime, endTime))
            else:   # Doesn't involve midnight
               subAnswers = subAnswers + str(iottime.IsTimeBetween(startTime, nowTime, endTime))
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
    if subAnswers != "":
        #log.debug("About to evaluate:'"+subAnswers+"'")
        try:
            finalAnswer = eval(subAnswers)
        except: # Catch all errors that the rule might raise
            err = sys.exc_info()[0]
            status.problem("Bad rule : '" + join(ruleConditionList) + "'", err) # Make a note in the status page so the user can fix the rule
            finalAnswer = False # Say rule failed
        return finalAnswer
    else:
        return False    # Empty string is always False

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
        elif ":" in tstVal:
            varVal = iottime.Sanitise(varVal)   # Ensure timestamps are consistently formatted before comparing (to avoid "0:15" != "00:15")
            tstVal = iottime.Sanitise(tstVal)
        else:
            varVal = "'"+varVal.lower() + "'"
            tstVal = "'"+tstVal.lower() + "'"   # Surround strings with quotes to make string comparisons work (Tuesday==Tuesday fails, although 'Tuesday'=='Tuesday' works)
        condStr = varVal + test + tstVal
        try:
            answer = eval(condStr)
        except:
            status.problem("BadRule", "Failed to evaluate '" + condStr + "'")
            log.debug("Failed to evaluate '" + condStr + "'")
            answer = False  # Default answer to allow rest of rules to continue to run
        return answer
    else:
        return False # If we couldn't find the item requested, assume the condition fails(?)

def Action(actList):
    log.debug("Action with: "+str(actList))
    action = actList[0].lower()
    if action == "Log".lower():
        log.debug("Rule says Log event for "+' '.join(actList[1:]))
    elif action == "Play".lower():
        call(["omxplayer", "-o", actList[1], actList[2]])
    elif action == "Event".lower():
        if actList[1].lower() == "TimeOfDay".lower():
            events.IssueEvent(events.ids.TIMEOFDAY, actList[2])
        elif actList[1].lower() == "Alarm".lower():
            events.IssueEvent(events.ids.ALARM, actList[2])
        # Could have other events here...
    elif action == "status":  # Was synopsis
        emailAddress = config.Get("emailAddress")
        if emailAddress != None:
            with open("status.email", "r") as status:   # Plain text of email
                emailText = status.readlines()
            text = ''.join(emailText)
            with open("status.html", "r") as status:    # HTML of email
                emailHtml = status.readlines()
            html = ''.join(emailHtml)
            sendmail.email("Vesta Status", text, html)
    elif action == "email": # All args are body of the text.  Fixed subject and email address
        emailAddress = config.Get("emailAddress")
        if emailAddress != None:
            emailBody = []
            for item in actList[1:]:
                emailBody.append(item)
            plainText = join(emailBody)
            sendmail.email("Vesta Alert!", plainText, None)
    elif action == "set":   # Set a named variable to a value
        expression = "".join(actList[1:])   # First recombine actList[1] onwards, with no spaces.  Now expression should be of the form "<var>=<val>"
        if "--" in expression:
            sep = expression.index("--")
            varName = expression[:sep]
            varVal = variables.Get(varName)
            if isNumber(varVal):
                newVal = str(eval(varVal+"-1"))
                variables.Set(varName, newVal)
            else:
                log.fault(varName+" not a number at "+expression)
        elif "=" in expression:
            sep = expression.index("=")
            varName = expression[:sep]
            varVal = expression[sep+1:]
            variables.Set(varName, varVal)
        else:
            log.fault("Badly formatted rule at "+expression)
    elif action == "unset":   # Remove a named variable
        variables.Del(actList[1])
    else: # Must be a command for a device, or group of devices
        name = actList[1]   # Second arg is name
        if database.IsGroupName(name): # Check if name is a groupName
            devKeyList = GetGroupDevs(name)
            for devKey in devKeyList:
                CommandDev(action, devKey, actList) # Command each device in list
        else:
            devKey = database.GetDevKey("userName", name)
            CommandDev(action, devKey, actList) # Command one device

def CommandDev(action, devKey, actList):
    if devKey == None:
        log.fault("Device "+actList[1]+" from rules not found in devices")
        status.problem("rules", "Unknown device "+actList[1]+" in rules")
    else:
        if action == "SwitchOn".lower():
            devcmds.SwitchOn(devKey)
            if len(actList) > 3:
                if actList[2] == "for":
                    SetOnDuration(devKey, int(actList[3],10))
        elif action == "SwitchOff".lower():
            devcmds.SwitchOff(devKey)
        elif action == "Toggle".lower():
            devcmds.Toggle(devKey)
        elif action == "Dim".lower() and actList[2] == "to":
            devcmds.Dim(devKey,float(actList[3]))
            if len(actList) > 5:
                if actList[4] == "for":
                    SetOnDuration(devKey, int(actList[5],10))
        elif action == "HueSat".lower():    # Syntax is "do HueSat <Hue in degrees>,<fractional saturation>
            devcmds.Colour(devKey, int(actList[3],10), float(actList[4]))
        else:
            log.debug("Unknown action: "+action +" for device: "+actList[1])

def SetOnDuration(devKey, durationS):
    if durationS>0: # Duration of 0 means "Stay on forever"
        log.debug("Switching off after "+str(durationS))
        devices.SetTempVal(devKey, "SwitchOff@", datetime.now()+timedelta(seconds=durationS))

