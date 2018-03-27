# presence.py

from datetime import datetime
from datetime import timedelta
import random
# App-specific modules
import events
import devices
import devcmds
import database
import log

class states():
    unknown = "Unknown"
    absent = "MISSING"
    present = "Present"

def EventHandler(eventId, eventArg):
    if eventId == events.ids.NEWDEVICE:
        devKey = eventArg
        Set(devKey, states.present)   # Mark any new device as immediately present
    if eventId == events.ids.MINUTES:
        Check()   # For all devices

def Check():  # Expected to be called infrequently - ie once/minute
    keyList = database.GetAllDevKeys()  # Get a list of all the device identifiers from the database
    notHeardFromList = []
    for devKey in keyList:  # Element 0 is hub, rest are devices
        if database.GetDeviceItem(devKey, "nwkId") != "0000":  # Ignore hub
            lastSeen, presence = Get(devKey)
            if datetime.now() > lastSeen+timedelta(seconds=900) and "SED" != database.GetDeviceItem(devKey, "devType"): # More than 15 minutes since we last heard from device, and it's listening
                notHeardFromList.append(devKey)    # Make a list of devices to query
            if presence != states.absent and datetime.now() > lastSeen+timedelta(seconds=1800): # More than 30 minutes since we last heard from device
                Set(devKey, states.absent)
            if presence == states.absent:
                notHeardFromList.append(devKey)    # Make a list of devices to query
    if notHeardFromList != []:
        numDevs = len(notHeardFromList)
        if numDevs > 3:
            for i in range(3):  # Prod 3 random devices from list
                devcmds.Prod(random.choice(notHeardFromList))    # Ask device a question, just to provoke a response
        else:   # Prod each device in list
            for devKey in notHeardFromList:
                devcmds.Prod(devKey)    # Ask device a question, just to provoke a response

def Set(devKey, newState):
    if newState == states.absent:
        database.LogItem(devKey, "SignalPercentage", 0) # Clear down signal strength when device goes missing
    database.LogItem(devKey, "Presence", newState)

def Get(devKey):
    entry = database.GetLatestLoggedItem(devKey, "Presence")
    if entry != None:
        #log.debug("Presence entry says " + str(entry))
        return datetime.strptime(entry[1], "%Y-%m-%d %H:%M:%S"), entry[0]   # Should be time, val
    else:
        Set(devKey, states.unknown) # Set up an entry for this device for use in future
        return datetime.now(), states.unknown # Return something for now

def GetAvailability(devKey):    # Over last 24 hours
    lastSeen, presence = Get(devKey)
    userName = database.GetDeviceItem(devKey, "userName")
    if userName == None:
        return "Unknown name for device"
    if lastSeen < datetime.now()-timedelta(hours=24):   # Check if any change in last 24 hours
        if presence == states.present:
            availability = ""   # Perfect availability for the whole time
        else:   # Assume absent
            availability = userName + " has been missing all day"
    else:   # There's been some changes in presence in the last 24 hours
        entries = database.GetLoggedItemsSinceTime(devKey, "Presence", "datetime('now', '-1 day')")
        #log.debug(userName+"'s presence for last 24 hours;"+str(entries))
        if entries == None:
            availability = "No presence for "+userName
        elif len(entries) == 1:   # The device has changed only once in the last 24 hours
            lastTwoEntries = database.GetLastNLoggedItems(devKey, "Presence", 2)   # Get last 2 entries
            if len(lastTwoEntries) == 1:   # The device has changed only once ever
                availability = ""   # Perfect availability for the whole time
            else:   # Check when it changed, and what it changed to to work out 
                availability = ""   # Hasn't changed enough to be a worry
        elif len(entries) > 1:
            availability = userName + "'s availability changed "+str(len(entries))+" times in last 24 hours and is now "+presence   # Changeable
        else:
            if presence == states.present:
                availability = ""   # Perfect availability for the whole time
            else:   # Assume absent or unknown
                availability = userName + " has not been heard from all day"
    return availability


