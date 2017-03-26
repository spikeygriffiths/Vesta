# presence.py

from datetime import datetime
from datetime import timedelta
# App-specific modules
import devices
import database
import zcl
import telegesis
import log

class states():
    unknown = "Unknown"
    absent = "Absent"
    present = "Present"

def Init():
    numDevs = database.GetDevicesCount()
    for devIdx in range(1, numDevs):  # Element 0 is hub, so skip that
        Set(devIdx, states.unknown)

def Check():  # Expected to be called infrequently - ie once/minute
    numDevs = database.GetDevicesCount()
    for devIdx in range(1, numDevs):  # Element 0 is hub, so skip that
        if devices.GetTempVal(devIdx, "AtCmdRsp") == None:  # No pending command, so check whether device is present
            presence = Get(devIdx)
            if presence != states.absent:
                lastSeen = devices.GetTempVal(devIdx, "LastSeen") 
                if lastSeen != None:
                    if datetime.now() > lastSeen+timedelta(seconds=900) or (presence == states.unknown and "SED"!= database.GetDeviceItem(devIdx, "devType")): # More than 15 minutes since we last heard from device, or it's unknown and listening
                        devId = database.GetDeviceItem(devIdx, "nwkId")
                        ep = database.GetDeviceItem(devIdx, "endPoints")
                        if devId != None and ep != None:
                            pendingAtCmd = telegesis.ReadAttr(devId, ep, zcl.Cluster.Basic, zcl.Attribute.Model_Name) # Get Basic's Device Name in order to prod it into life
                            devices.SetTempVal(devIdx, "AtCmdRsp", pendingAtCmd)
                    if datetime.now() > lastSeen+timedelta(seconds=1800): # More than 30 minutes since we last heard from device
                        Set(devIdx, states.absent)

def Set(devIdx, newState):
    devices.SetStatus(devIdx, "Presence", newState)

def Get(devIdx):
    return database.GetLatestEvent(devIdx, "Presence")

