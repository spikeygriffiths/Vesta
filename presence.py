# presence.py

from datetime import datetime
from datetime import timedelta
# App-specific modules
import devices
import database
import log

class states():
    unknown = "Unknown"
    absent = "Absent"
    present = "Present"

def Check():  # Expected to be called infrequently - ie once/minute
    numDevs = database.GetDevicesCount()
    for devIdx in range(1, numDevs):  # Element 0 is hub, so skip that
        presence, lastSeen = Get(devIdx)
        if presence != states.absent:
            #devlastSeen = devices.GetTempVal(devIdx, "LastSeen")
            #log.debug("In presence.Check, presence="+presence+", lastSeen="+str(lastSeen)+" for devIdx "+str(devIdx)+". tempValLastSeen="+str(devlastSeen))
            if lastSeen != None:
                if datetime.now() > lastSeen+timedelta(seconds=900) or (presence == states.unknown and "SED"!= database.GetDeviceItem(devIdx, "devType")): # More than 15 minutes since we last heard from device, or it's unknown and listening
                    devices.Prod(devIdx)    # Ask device a question, just to provoke a response                        
                if datetime.now() > lastSeen+timedelta(seconds=1800): # More than 30 minutes since we last heard from device
                    Set(devIdx, states.absent)

def Set(devIdx, newState):
    database.SetStatus(devIdx, "presence", newState)

def Get(devIdx):
    return database.GetStatus(devIdx, "presence")

