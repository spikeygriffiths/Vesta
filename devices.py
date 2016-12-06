# ./devices

from datetime import datetime
import json
# App-specific modules
import events
import hubapp

if __name__ == "__main__":
    hubapp.main()

devFilename = "devices.json"
dirty = False

# Keep a track of known devices present in the system
info = []

def EventHandler(eventId, arg):
    global dirty
    if eventId == events.ids.INIT:
        with open(devFilename, "r") as f:
            info = json.load(f) # Load previous cache of devices into info[]
    if eventId == events.ids.CHECKIN:
        # See if we have anything to ask the device...
        devIdx = FindAdd(arg[2])
        SetVal(devIdx, "LastSeen", datetime.now())  # Mark it as "recently seen"
        atCmd = check(devIdx)   # Check to see if we want to know anything about the device
        if atCmd != "":
            telegesis.TxCmd(atCmd)  # And also ought to tell device to keep polling...
    if eventId = events.ids.SECONDS:
        if dirty:
            with open(devFilename, "w") as f:
                json.dump(info, f)
            dirty = False   # Don't save again until needed
        

def FindAdd(devId):
    devIdx = Find(devId)
    if -1 == devIdx:
        devIdx = NewDev(devId)
    return devIdx

def Find(devId):
    devIdx = 0
    for device in info:
        for item in device:
            if item == ("devId", devId):
                return devIdx
        devIdx = devIdx + 1
    return -1 # Failed to find device

def NewDev(devId):
    info.append([("devId",devId)])
    dirty = True # Note that we need to serialize the device info soon
    return len(info)-1 # -1 to convert number of elements in list to an index

def SetVal(devIdx, name, value):
    for item in info[devIdx]:
        if item[0] == name:
            info[devIdx].remove(item) # Remove old tuple if necessary
    info[devIdx].append((name, value) ) # Add new one regardless
    dirty = True # Note that we need to serialize the device info soon
    
def GetVal(devIdx, name):
    for item in info[devIdx]:
        if item[0] == name:
            return item[1] # Just return value
    return "" # Empty string to indicate item not found
