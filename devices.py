#!devices.py

from datetime import datetime
from datetime import timedelta
import json
# App-specific modules
import events
import log
import hubapp
import telegesis

if __name__ == "__main__":
    hubapp.main()

devFilename = "devices_cache"
dirty = False

# Keep a track of known devices present in the system
info = []

def EventHandler(eventId, arg):
    global info, dirty
    if eventId == events.ids.INIT:
        try:
            with open(devFilename, "r") as f:
                try:
                    info = eval(f.read()) # Load previous cache of devices into info[]
                    log.log("Loaded list from file")
                except:
                    log.fault("Unusable device list from file - discarding!")
                    info = []
        except OSError:
            info = []
        dirty = False   # Info[] is initialised now
    if eventId == events.ids.NEWDEV:
        devId = arg[2]
        devIdx = GetIdx(devId) # Will create new device if not found in earlier list
        NoteEphemera(devIdx, arg)
        SetVal(devIdx,"DevType",arg[0])    # SED, FFD or ZED
        SetVal(devIdx,"EUI",arg[1])
        if arg[0] == "SED":
            SetVal(devIdx,"PollingUntil", datetime.now()+timedelta(seconds=300))
    if eventId == events.ids.CHECKIN:   # See if we have anything to ask the device...
        devId = arg[1]
        endPoint = arg[2]
        seq = arg[3]
        devIdx = GetIdx(devId)
        NoteEphemera(devIdx, arg)
        if GetVal(devIdx, "EP") == None:
            SetVal(devIdx, "EP", endPoint) # Note endpoint that CheckIn came from, unless we already know this
        atCmd = Check(devIdx)   # Check to see if we want to know anything about the device
        if atCmd != None:
            telegesis.TxCmd("AT+RAWZCL:"+devId+","+endPoint+",0020,11"+seq+"00012800") # Tell device to enter Fast Poll for 40qs (==10s)
            SetVal(devIdx,"PollingUntil", datetime.now()+timedelta(seconds=10))
            telegesis.TxCmd(atCmd)  # This will go out after the Fast Poll Set
        else:
            telegesis.TxCmd("AT+RAWZCL:"+devId+","+endPoint+",0020,11"+seq+"0000") # Tell device to stop Poll
    if eventId == events.ids.RXMSG:
        if arg[0] == "AddrResp" and arg[1] == "00":
            devIdx = GetIdx(arg[2])
            SetVal(devIdx,"EUI",arg[3])
        elif arg[0] == "ActEpDesc":
            if "00" == arg[2]:
                devIdx = GetIdx(arg[1])
                SetVal(devIdx, "EP", arg[2]) # Note first endpoint                
        if arg[0] == "RESPATTR":
            devIdx = GetIdx(arg[1])
            ep = arg[2]
            clusterId = arg[3]
            attrId = arg[4]
            if "00" == arg[5]:
                attrVal = arg[6]
                SetAttrVal(devIdx, clusterId, attrId, attrVal)
        if arg[0] == "REPORTATTR":
            devIdx = GetIdx(arg[1])
            ep = arg[2]
            clusterId = arg[3]
            attrId = arg[4]
            attrType = arg[5]
            attrVal = arg[6]
            NoteEphemera(devIdx, arg)
            SetAttrVal(devIdx, clusterId, attrId, attrVal)
    if eventId == events.ids.SECONDS:
        atCmd = CheckAll()
        if atCmd != None:
            telegesis.TxCmd(atCmd)
        if dirty:
            with open(devFilename, "w") as f:
                print(info, file=f) # Save devices list directly to file
            dirty = False   # Don't save again until needed
    # End event handler

def GetIdx(devId):
    idx = GetIdxFromItem("devId", devId)
    if idx:
        return idx
    else:
        return InitDev(devId) # Special case of devId search automatically initialising a new device if necessary

def GetIdxFromItem(item, value):
    global info
    devIdx = 0
    for device in info:
        for item in device:
            if item == (item, value):
                return devIdx
        devIdx = devIdx + 1
    return None # Item not found

def GetIdxFromUsername(userName):
    return GetIdxFromItem("userName", userName)
    
def InitDev(devId):
    log.log("New devId:"+ str(devId)+"added to list"+ str(info))
    info.append([])  # If we didn't find it, then add empty device
    devIdx = len(info)-1 # -1 to convert number of elements in list to an index
    SetVal(devIdx,"devId",devId)
    return devIdx

def SetVal(devIdx, name, value):
    global info, dirty
    for item in info[devIdx]:
        if item[0] == name:
            info[devIdx].remove(item) # Remove old tuple if necessary
    info[devIdx].append((name, value)) # Add new one regardless
    dirty = True # Note that we need to serialize the device info soon
    
def GetVal(devIdx, name):
    global info
    for item in info[devIdx]:
        if item[0] == name:
            return item[1] # Just return value associated with name
    return None # Indicate item not found

def DelVal(devIdx, name):
    global info
    for item in info[devIdx]:
        if item[0] == name:
            oldValue = item[1]
            info[devIdx].remove(item) # Remove old tuple if necessary
            return oldValue # Just return old value associated with name before it was deleted
    return None # Indicate item not found

def SetAttrVal(devIdx, clstrId, attrId, value):
    name = "attr"+clstrId+":"+attrId # So that the id combines cluster as well as attribute
    SetVal(devIdx, name, value) # Keep it simple

def GetAttrVal(devIdx, clstrId, attrId):
    name = "attr"+clstrId+":"+attrId # So that the id combines cluster as well as attribute
    return GetVal(devIdx, name)

def NoteEphemera(devIdx, arg):
    SetVal(devIdx, "LastSeen", datetime.now().strftime("%y/%m/%d %H:%M:%S"))  # Mark it as "recently seen"
    if int(arg[-2]) < 0: # Assume penultimate item is RSSI, and thus that ultimate one is LQI
        SetVal(devIdx, "RSSI", arg[-2])
        SetVal(devIdx, "LQI", arg[-1])

def Check(devIdx):
    devId = GetVal(devIdx, "devId")
    ep = GetVal(devIdx, "EP")
    if None == GetVal(devIdx, "EUI"):
        return "AT+EUIREQ:"+devId+","+devId
    if None == GetVal(devIdx, "EP"):
        return "AT+ACTEPDESC:"+devId+","+devId
    if None == GetAttrVal(devIdx, "0000","0005"):
        return "AT+READATR:"+devId+","+ep+",0,0000,0005" # Get Basic's Device Name
    if None == GetAttrVal(devIdx, "0000","0004"):
        return "AT+READATR:"+devId+","+ep+",0,0000,0004" # Get Basic's Manufacturer Name
    pendingAtCmd = GetVal(devIdx, "AtCmd")
    if pendingAtCmd:
        DelVal(devIdx,"AtCmd") # Remove item now that we're actioning it
        return pendingAtCmd

def CheckAll():
    global info
    devIdx = 0
    for device in info:
        for item in device:
            if IsListening(devIdx):# True if FFD, ZED or Polling
                atCmd = Check(devIdx)
                if atCmd != None:
                    return atCmd
        devIdx = devIdx + 1

def IsListening(devIdx):
    type = GetVal(devIdx, "DevType")
    if type == "FFD" or type == "ZED":
        return True # These devices are always awake and listening
    else: # Assume sleepy, so check if polling
        ##pollTime = GetVal(devIdx, "PollingUntil")
        ##if pollTime != None:
        ##    if datetime.now() < pollTime:
        ##        log.log("Now:"+ str(datetime.now()))
        ##        return True
        return False

def SwitchOn(devIdx, durationS):
    devId = GetVal(devIdx, "devId")
    ep = GetVal(devIdx, "EP")
    if devId and ep:
        telegesis.TxCmd("AtCmd", "AT+RONOFF:"+devId+","+ep+",0,1") # Assume FFD if it supports OnOff cluster
        if durationS>0: # Duration of 0 means "Stay on forever"
            SetVal(devIdx, "SwitchOff@", datetime.now()+timedelta(seconds=durationS))

def SwitchOff(devIdx):
    devId = GetVal(devIdx, "devId")
    ep = GetVal(devIdx, "EP")
    if devId and ep:
        DelVal(devIdx,"SwitchOff@") # Remove any pending "Off" events if we're turning the device off directly
        telegesis.TxCmd("AtCmd", "AT+RONOFF:"+devId+","+ep+",0,0") # Assume FFD if it supports OnOff cluster

def Toggle(devIdx):
    devId = GetVal(devIdx, "devId")
    ep = GetVal(devIdx, "EP")
    if devId and ep:
        DelVal(devIdx,"SwitchOff@") # Remove any pending "Off" events if we're handling the device directly
        telegesis.TxCmd("AtCmd", "AT+RONOFF:"+devId+","+ep+",0") # Assume FFD if it supports OnOff cluster

def FadeOn(devIdx, levelPercent, durationS):
    devId = GetVal(devIdx, "devId")
    ep = GetVal(devIdx, "EP")
    if devId and ep:
        levelStr = format((levelPercent * 2.55), 'X')
        telegesis.TxCmd("AtCmd", "AT+LCMVTOLEV:"+devId+","+ep+",0,0,"+levelStr+",0A00") # Fade over 1 sec (in 10ths)
        if durationS>0: # Duration of 0 means "Stay on forever"
            SetVal(devIdx, "SwitchOff@", datetime.now()+timedelta(seconds=durationS)) # Could be "FadeOff"

