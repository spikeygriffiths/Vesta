# ./devices

from datetime import datetime
import json
# App-specific modules
import events
import hubapp
import telegesis

if __name__ == "__main__":
    hubapp.main()

devFilename = "devices.json"
dirty = False

# Keep a track of known devices present in the system
info = []

def EventHandler(eventId, arg):
    global info, dirty
    if eventId == events.ids.INIT:
        try:
            with open(devFilename, "r") as f:
                info = json.load(f) # Load previous cache of devices into info[]
        except OSError:
            info = []
        dirty = False   # Info[] is initialised now
    if eventId == events.ids.CHECKIN:
        # See if we have anything to ask the device...
        devIdx = GetIdx(arg[1])
        SetVal(devIdx, "LastSeen", datetime.now().strftime("%y/%m/%d %H:%M:%S"))  # Mark it as "recently seen"
        atCmd = Check(devIdx)   # Check to see if we want to know anything about the device
        if atCmd != "":
            telegesis.TxCmd(atCmd)  # And also ought to tell device to keep polling...
    if eventId == events.ids.SECONDS:
        if dirty:
            with open(devFilename, "w") as f:
                json.dump(info, f)
            dirty = False   # Don't save again until needed
    if eventId == events.ids.RXMSG:
        if arg[0] == "AddrResp" and arg[1] == "00":
            devIdx = FindAdd(arg[2])
            devices.SetVal(devIdx,"EUI",arg[3])
        
        

def GetIdx(devId):
    global info, dirty
    devIdx = 0
    for device in info:
        for item in device:
            if item == ("devId", devId):
                return devIdx
        devIdx = devIdx + 1
    info.append([("devId",devId)])  # If we didn't find it, then add it
    dirty = True # Note that we need to serialize the device info soon
    return len(info)-1 # -1 to convert number of elements in list to an index

def SetVal(devIdx, name, value):
    global info, dirty
    for item in info[devIdx]:
        if item[0] == name:
            info[devIdx].remove(item) # Remove old tuple if necessary
    info[devIdx].append((name, value) ) # Add new one regardless
    dirty = True # Note that we need to serialize the device info soon
    
def GetVal(devIdx, name):
    global info
    for item in info[devIdx]:
        if item[0] == name:
            return item[1] # Just return value associated with name
    return "" # Empty string to indicate item not found

def Check(devIdx):
    devId = GetVal(devIdx, "devId")
    if "" == GetVal(devIdx, "EUI"):
        return "AT+EUIREQ:"+devId+","+devId
        
