# presence.py

from datetime import datetime
from datetime import timedelta
# App-specific modules
import events
import devices
import devcmds
import database
import log
import status

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
    for devKey in keyList:  # Element 0 is hub, rest are devices
        if database.GetDeviceItem(devKey, "nwkId") != "0000":  # Ignore hub
            lastSeen, presence = Get(devKey)
            if presence != None:    # It may have only just joined and still be unintialised (?)
                if presence != states.absent:
                    if datetime.now() > lastSeen+timedelta(seconds=900) or (presence == states.unknown and "SED"!= database.GetDeviceItem(devKey, "devType")): # More than 15 minutes since we last heard from device, or it's unknown and listening
                        devcmds.Prod(devKey)    # Ask device a question, just to provoke a response                        
                    if datetime.now() > lastSeen+timedelta(seconds=1800): # More than 30 minutes since we last heard from device
                        Set(devKey, states.absent)

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
        return datetime.now(), states.unknown

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
        if entries == None:
            return "No presence for "+userName
        if len(entries) == 1:   # The device has changed only once in the last 24 hours
            entries = database.GetLastNLoggedItems(devKey, "Presence", 2)   # Get last 2 entries
            if len(entries) == 1:   # The device has changed only once ever
                availability = ""   # Perfect availability for the whole time
            else:   # Check when it changed, and what it changed to to work out 
                availability = userName + " changed to "+presence+" since yesterday"   # Changeable
        else:
            availability = userName + "'s availability changed "+str(len(entries))+" times in last 24 hours and is now "+presence   # Changeable
    return availability


