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

presenceFreq = {}
absenceFreq = {}

def EventHandler(eventId, eventArg):
    if eventId == events.ids.INIT:
        keyList = database.GetAllDevKeys()  # Get a list of all the device identifiers from the database
        for devKey in keyList:  # Hub and devices
            if database.GetDeviceItem(devKey, "nwkId") != "0000":  # Ignore hub
                Set(devKey, states.unknown)
            else:   # Is hub, so must be Present
                Set(devKey, states.present)
    if eventId == events.ids.NEWDEVICE:
        devKey = eventArg
        Set(devKey, states.present)   # Mark any new device as immediately present
    if eventId == events.ids.MINUTES:
        Check()   # For all devices

def Check():  # Expected to be called infrequently - ie once/minute
    keyList = database.GetAllDevKeys()  # Get a list of all the device identifiers from the database
    for devKey in keyList:  # Element 0 is hub, rest are devices
        if database.GetDeviceItem(devKey, "nwkId") != "0000":  # Ignore hub
            presence, lastSeen = Get(devKey)
            if presence != None:    # It may have only just joined and still be unintialised (?)
                if presence == states.present:  # Check database each minute to build up a picture of how often each device is present or absent
                    if presenceFreq.get(devKey) != None:
                        presenceFreq[devKey] = presenceFreq[devKey] + 1
                    else:
                        presenceFreq[devKey] = 1
                elif presence == states.absent:
                    if absenceFreq.get(devKey) != None:
                        absenceFreq[devKey] = absenceFreq[devKey] + 1
                    else:
                        absenceFreq[devKey] = 1
                if presence != states.absent:
                    if datetime.now() > lastSeen+timedelta(seconds=900) or (presence == states.unknown and "SED"!= database.GetDeviceItem(devKey, "devType")): # More than 15 minutes since we last heard from device, or it's unknown and listening
                        devcmds.Prod(devKey)    # Ask device a question, just to provoke a response                        
                    if datetime.now() > lastSeen+timedelta(seconds=1800): # More than 30 minutes since we last heard from device
                        Set(devKey, states.absent)

def Set(devKey, newState):
    if newState == states.absent:
            database.SetStatus(devKey, "signal", 0) # Clear down signal strength when device goes missing
    database.SetStatus(devKey, "presence", newState)

def Get(devKey):
    return database.GetStatus(devKey, "presence")

def GetFreq(devKey):
    if presenceFreq.get(devKey) != None:
        presence = presenceFreq.get(devKey)
        if absenceFreq.get(devKey) != None:
            absence = absenceFreq.get(devKey)
        else:
            absence = 0 # Never absent
        presencePercentage = ((presence + absence) / presence) * 100
    else:
        if absenceFreq.get(devKey) != None:
            presencePercentage = 0  # Never present, but we have decided we've been absent more than once
        else:
            presencePercentage = -1 # No information about presence or absence yet...
    return presencePercentage

def ClearFreqs():
    presenceFreq.clear()
    absenceFreq.clear()

