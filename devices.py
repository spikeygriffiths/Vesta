# ./devices

from datetime import datetime
import json
# App-specific modules
import events
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
                    info = json.load(f) # Load previous cache of devices into info[]
                except:
                    info = []
        except OSError:
            info = []
        dirty = False   # Info[] is initialised now
    if eventId == events.ids.CHECKIN:
        # See if we have anything to ask the device...
        devIdx = GetIdx(arg[1])
        SetVal(devIdx, "LastSeen", datetime.now().strftime("%y/%m/%d %H:%M:%S"))  # Mark it as "recently seen"
        atCmd = Check(devIdx)   # Check to see if we want to know anything about the device
        if atCmd != None:
            telegesis.TxCmd("AT+FPSET:01,0028") # Tell device to enter Fast Poll for 40qs (==10s)
            telegesis.TxCmd(atCmd)  # This will go out after the Fast Poll Set
        else:
            telegesis.TxCmd("AT+FPSET:00") # Tell device to stop Poll
    if eventId == events.ids.SECONDS:
        if dirty:
            with open(devFilename, "w") as f:
                print(info, file=f) # was json.dump(info, f), but that converts tuples into lists
            dirty = False   # Don't save again until needed
    if eventId == events.ids.RXMSG:
        if arg[0] == "AddrResp" and arg[1] == "00":
            devIdx = GetIdx(arg[2])
            SetVal(devIdx,"EUI",arg[3])
    # End event handler
        

def GetIdx(devId):
    global info
    devIdx = 0
    for device in info:
        for item in device:
            if item == ("devId", devId):
                print ("Found devId at index", devIdx)
                return devIdx
        devIdx = devIdx + 1
    print ("New devId:", devId,"added to list", info)
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
    return "" # Empty string to indicate item not found

def Check(devIdx):
    devId = GetVal(devIdx, "devId")
    if "" == GetVal(devIdx, "EUI"):
        return "AT+EUIREQ:"+devId+","+devId
        
