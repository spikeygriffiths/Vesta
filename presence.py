# presence.py

from datetime import datetime
from datetime import timedelta
# App-specific modules
import devices
import devcmds
import database
import log

class states():
    unknown = "Unknown"
    absent = "Absent"
    present = "Present"

def Check():  # Expected to be called infrequently - ie once/minute
    keyList = database.GetAllDevKeys()  # Get a list of all the device identifiers from the database
    for devKey in keyList:  # Element 0 is hub, rest are devices
        if database.GetDeviceItem(devKey, "nwkId") != "0000":  # Ignore hub
            presence, lastSeen = Get(devKey)
            if presence != states.absent:
                if datetime.now() > lastSeen+timedelta(seconds=900) or (presence == states.unknown and "SED"!= database.GetDeviceItem(devKey, "devType")): # More than 15 minutes since we last heard from device, or it's unknown and listening
                    devcmds.Prod(devKey)    # Ask device a question, just to provoke a response                        
                if datetime.now() > lastSeen+timedelta(seconds=1800): # More than 30 minutes since we last heard from device
                    Set(devKey, states.absent)

def Set(devKey, newState):
    database.SetStatus(devKey, "presence", newState)

def Get(devKey):
    return database.GetStatus(devKey, "presence")

