# ./devices

from datetime import datetime
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
                    log.log("Initialised empty device list")
                    info = []
        except OSError:
            info = []
        dirty = False   # Info[] is initialised now
    if eventId == events.ids.CHECKIN:   # See if we have anything to ask the device...
        devId = arg[1]
        endPoint = arg[2]
        seq = arg[3]
        rssi = arg[4]
        lqi = arg[5]
        devIdx = GetIdx(devId)
        SetVal(devIdx, "LastSeen", datetime.now().strftime("%y/%m/%d %H:%M:%S"))  # Mark it as "recently seen"
        SetVal(devIdx, "EP", endPoint) # Note endpoint that CheckIn came from
        SetVal(devIdx, "RSSI", rssi)
        SetVal(devIdx, "LQI", lqi)
        atCmd = Check(devIdx)   # Check to see if we want to know anything about the device
        if atCmd != None:
            telegesis.TxCmd("AT+RAWZCL:"+devId+","+endPoint+",0020,00"+seq+"00010028") # Tell device to enter Fast Poll for 40qs (==10s)
            telegesis.TxCmd(atCmd)  # This will go out after the Fast Poll Set
        else:
            telegesis.TxCmd("AT+RAWZCL:"+devId+","+endPoint+",0020,00"+seq+"00") # Tell device to stop Poll
    if eventId == events.ids.SECONDS:
        if dirty:
            with open(devFilename, "w") as f:
                print(info, file=f) # Save devices list directly to file
            dirty = False   # Don't save again until needed
    if eventId == events.ids.RXMSG:
        if arg[0] == "AddrResp" and arg[1] == "00":
            devIdx = GetIdx(arg[2])
            SetVal(devIdx,"EUI",arg[3])
        if arg[0] == "RESPATTR":
            devIdx = GetIdx(arg[1])
            ep = arg[2]
            clusterId = arg[3]
            attrId = arg[4]
            if "00" == arg[5]:
                attrVal = arg[6]
                SetAttrVal(devIdx, clusterId, attrId, attrVal)
    # End event handler
        
def GetIdx(devId):
    global info
    devIdx = 0
    for device in info:
        for item in device:
            if item == ("devId", devId):
                log.log ("Found devId at index"+ str(devIdx))
                return devIdx
        devIdx = devIdx + 1
    return InitDev(devId) # Start a new device if requested one not found
    
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

def SetAttrVal(devIdx, clstrId, attrId, value):
    name = "attr"+clstrId+":"+attrId # So that the id combines cluster as well as attribute
    SetVal(devIdx, name, value) # Keep it simple

def GetAttrVal(devIdx, clstrId, attrId):
    name = "attr"+clstrId+":"+attrId # So that the id combines cluster as well as attribute
    return GetVal(devIdx, name)

def Check(devIdx):
    devId = GetVal(devIdx, "devId")
    ep = GetVal(devIdx, "EP")
    if None == GetVal(devIdx, "EUI"):
        return "AT+EUIREQ:"+devId+","+devId
    if None == GetVal(devIdx, "Name"):
        return "AT+READATR:"+devId+","+ep+",0,0000,0004" # Get Basic's Name
        
