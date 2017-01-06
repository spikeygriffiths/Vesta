#!devices.py

from datetime import datetime
from datetime import timedelta
# App-specific modules
import events
import log
import hubapp
import telegesis
import zcl

if __name__ == "__main__":
    hubapp.main()

devFilename = "devices_cache"
dirty = False
globalDevIdx = None
pendingBinding = None # Needed because the BIND response doesn't include the cluster
pendingRptAttrId = None # Needed because CFGRPTRSP only includes the cluster and not the attr

# Keep a track of known devices present in the system
info = []
ephemera = [] # Don't bother saving this

def EventHandler(eventId, arg):
    global info, dirty, globalDevIdx, pendingBinding, pendingRptAttrId
    if eventId == events.ids.INIT:
        try:
            with open(devFilename, "r") as f:
                try:
                    info = eval(f.read()) # Load previous cache of devices into info[]
                    for devices in info:
                        ephemera.append([]) # Initialise parallel ephemeral device list
                    log.log("Loaded list from file")
                except:
                    log.fault("Unusable device list from file - discarding!")
                    info = []
        except OSError:
            info = []
        dirty = False   # Info[] is initialised now
    if eventId == events.ids.NEWDEV:
        devId = arg[2]
        devIdx = GetIdx(devId)
        if devIdx == None:  # Which ought to be the case
            devIdx = InitDev(devId)
        NoteEphemera(devIdx, arg)
        SetVal(devIdx,"DevType",arg[0])    # SED, FFD or ZED
        SetVal(devIdx,"EUI",arg[1])
        if arg[0] == "SED":
            SetTempVal(devIdx,"PollingUntil", datetime.now()+timedelta(seconds=300))
    if eventId == events.ids.CHECKIN:   # See if we have anything to ask the device...
        endPoint = arg[2]
        seq = arg[3]
        devIdx = GetIdx(arg[1])
        if devIdx != None:
            NoteEphemera(devIdx, arg)
            if GetVal(devIdx, "EP") == None:
                SetVal(devIdx, "EP", endPoint) # Note endpoint that CheckIn came from, unless we already know this
            devId = GetVal(devIdx, "devId")
            cmdRsp = Check(devIdx, False)   # Check to see if we want to know anything about the device
            if cmdRsp != None:
                telegesis.TxCmd(["AT+RAWZCL:"+devId+","+endPoint+",0020,11"+seq+"00012800", "OK"]) # Tell device to enter Fast Poll for 40qs (==10s)
                SetTempVal(devIdx,"PollingUntil", datetime.now()+timedelta(seconds=10))
                telegesis.TxCmd(cmdRsp)  # This will go out after the Fast Poll Set - but possibly ought to go out as part of SECONDS handler..?
            else:
                telegesis.TxCmd(["AT+RAWZCL:"+devId+","+endPoint+",0020,11"+seq+"0000", "OK"]) # Tell device to stop Poll
    if eventId == events.ids.RXMSG:
        if arg[0] == "AddrResp" and arg[1] == "00":
            devIdx = GetIdx(arg[2])
            if devIdx != None:
                SetVal(devIdx,"EUI",arg[3])
        elif arg[0] == "ActEpDesc":
            if "00" == arg[2]:
                devIdx = GetIdx(arg[1])
                if devIdx != None:
                    SetVal(devIdx, "EP", arg[2]) # Note first endpoint
        elif arg[0] == "SimpleDesc":
            if "00" == arg[2]:
                globalDevIdx = GetIdx(arg[1]) # Is multi-line response, so expect rest of response and use this global index until it's all finished
        elif arg[0] == "InCluster":
           if globalDevIdx != None:
             SetVal(globalDevIdx, "InCluster", arg[1:]) # Store whole list from arg[1] to arg[n]
        elif arg[0] == "OutCluster":
            if globalDevIdx != None:
                NoteEphemera(globalDevIdx, arg)
                SetVal(globalDevIdx, "OutCluster", arg[1:]) # Store whole list from arg[1] to arg[n]
            globalDevIdx = None # We've finished with this global for now
        if arg[0] == "RESPATTR":
            devIdx = GetIdx(arg[1])
            if devIdx != None:
                ep = arg[2]
                clusterId = arg[3]
                attrId = arg[4]
                if "00" == arg[5]:
                    attrVal = arg[6]
                else:
                    attrVal = "Error:"+arg[5]   # So that we don't ask for the same attribute again later
                SetAttrVal(devIdx, clusterId, attrId, attrVal)
        if arg[0] == "REPORTATTR":
            devIdx = GetIdx(arg[1])
            if devIdx != None:
                ep = arg[2]
                clusterId = arg[3]
                attrId = arg[4]
                attrType = arg[5]
                attrVal = arg[6]
                NoteEphemera(devIdx, arg)
                SetAttrVal(devIdx, clusterId, attrId, attrVal)
                reporting = GetVal(devIdx, "Reporting") # See if we're expecting this report, and note it in the reporting table
                newRpt = clusterId+":"+attrId
                if newRpt not in reporting:
                    reporting.append(newRpt)
                    SetVal(devIdx, "Reporting", reporting)
        if arg[0] == "Bind":    # Binding Response from device
            devIdx = GetIdx(arg[1])
            if devIdx != None:
                if pendingBinding != None:
                    binding = GetVal(devIdx, "Binding")
                    binding.append(pendingBinding)
                    SetVal(devIdx, "Binding", binding)
                    pendingBinding = None
        if arg[0] == "CFGRPTRSP":   # Configure Report Response from device
            devIdx = GetIdx(arg[1])
            status = arg[4]
            if devIdx != None and status == "00":
                clusterId = arg[3]
                attrId = pendingRptAttrId # Need to remember this, since it doesn't appear in CFGRPTRSP
                reporting = GetVal(devIdx, "Reporting")
                newRpt = clusterId+":"+attrId
                if newRpt not in reporting:
                    reporting.append(newRpt)
                    SetVal(devIdx, "Reporting", reporting)
    if eventId == events.ids.SECONDS:
        SendPendingCommand()
        if dirty:
            with open(devFilename, "w") as f:
                print(info, file=f) # Save devices list directly to file
            dirty = False   # Don't save again until needed
    # End event handler

def GetIdx(devId):
    idx = GetIdxFromItem("devId", devId)
    if idx != None:
        return idx
    else:
        log.fault("Unknown device " + devId)
        return None  # Was "return InitDev(devId) # Special case of devId search automatically initialising a new device if necessary" but it often failed

def GetIdxFromItem(name, value):
    global info
    devIdx = 0
    searchTerm = (name, value)
    #log.log("Searching for: " + str(searchTerm))
    for device in info:
        #log.log("Each device "+ str(device))
        for item in device:
            #log.log("Each item from device"+ str(item))
            if item == searchTerm:
                return devIdx
        devIdx = devIdx + 1
    return None # Item not found

def GetIdxFromUsername(userName):
    return GetIdxFromItem("userName", userName)
    
def InitDev(devId):
    global info
    log.log("Adding new devId: "+ str(devId))
    info.append([])  # If we didn't find it, then add empty device
    ephemera.append([]) # Add parallel ephemeral device list
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

def SetTempVal(devIdx, name, value):
    global ephemera
    for item in ephemera[devIdx]:
        if item[0] == name:
            ephemera[devIdx].remove(item) # Remove old tuple if necessary
    ephemera[devIdx].append((name, value)) # Add new one regardless
    
def GetTempVal(devIdx, name):
    global ephemera
    for item in ephemera[devIdx]:
        if item[0] == name:
            return item[1] # Just return value associated with name
    return None # Indicate item not found

def DelTempVal(devIdx, name):
    global ephemera
    for item in ephemera[devIdx]:
        if item[0] == name:
            oldValue = item[1]
            ephemera[devIdx].remove(item) # Remove old tuple if necessary
            return oldValue # Just return old value associated with name before it was deleted
    return None # Indicate item not found

def NoteEphemera(devIdx, arg):
    SetTempVal(devIdx, "LastSeen", datetime.now().strftime("%y/%m/%d %H:%M:%S"))  # Mark it as "recently seen"
    if int(arg[-2]) < 0: # Assume penultimate item is RSSI, and thus that ultimate one is LQI
        rssi = arg[-2]
        lqi = arg[-1]
        SetTempVal(devIdx, "RSSI", rssi)
        SetTempVal(devIdx, "LQI", lqi)
        arg.remove(rssi)
        arg.remove(lqi)

def Check(devIdx, consume):
    global pendingBinding, pendingRptAttrId
    devId = GetVal(devIdx, "devId")
    ep = GetVal(devIdx, "EP")
    if None == ep:
        return ("AT+ACTEPDESC:"+devId+","+devId, "ActEpDesc")
    if None == GetVal(devIdx, "EUI"):
        return ("AT+EUIREQ:"+devId+","+devId, "AddrResp")
    if None == GetVal(devIdx, "InCluster") or None == GetVal(devIdx, "OutCluster"):
        return ("AT+SIMPLEDESC:"+devId+","+devId+","+ep, "OutCluster")
    inClstr = GetVal(devIdx, "InCluster") # Assume we have a list of clusters if we get this far
    outClstr = GetVal(devIdx, "OutCluster")
    binding = GetVal(devIdx, "Binding")
    rprtg = GetVal(devIdx, "Reporting")
    if inClstr != None:
        if binding != None:
            eui = GetVal(devIdx, "EUI")
            if zcl.Cluster.PollCtrl in inClstr and zcl.Cluster.PollCtrl not in binding:
                pendingBinding = zcl.Cluster.PollCtrl
                return ("AT+BIND:"+devId+",3,"+eui+","+ep+","+zcl.Cluster.PollCtrl+","+telegesis.ourEui+",01", "Bind")
            if zcl.Cluster.OnOff in outClstr and zcl.Cluster.OnOff not in binding:
                pendingBinding = zcl.Cluster.OnOff
                return ("AT+BIND:"+devId+",3,"+eui+","+ep+","+zcl.Cluster.OnOff+","+telegesis.ourEui+",0A", "Bind")
            if zcl.Cluster.PowerConfig in inClstr and zcl.Cluster.PowerConfig not in binding:
                pendingBinding = zcl.Cluster.PowerConfig
                return ("AT+BIND:"+devId+",3,"+eui+","+ep+","+zcl.Cluster.PowerConfig+","+telegesis.ourEui+",01", "Bind")
            # Could add temperature binding here, if we also add temperature reporting
        else:
            SetVal(devIdx, "Binding", [])
        if zcl.Cluster.IAS_Zone in inClstr:
            if None == GetAttrVal(devIdx, zcl.Cluster.IAS_Zone, zcl.Attribute.Zone_Type):
                return telegesis.ReadAttr(devId, ep, zcl.Cluster.IAS_Zone, zcl.Attribute.Zone_Type)
        if zcl.Cluster.Basic in inClstr:
            if None == GetAttrVal(devIdx, zcl.Cluster.Basic, zcl.Attribute.Model_Name):
                return telegesis.ReadAttr(devId, ep, zcl.Cluster.Basic, zcl.Attribute.Model_Name) # Get Basic's Device Name
            if None == GetAttrVal(devIdx, zcl.Cluster.Basic, zcl.Attribute.Manuf_Name):
                return telegesis.ReadAttr(devId, ep, zcl.Cluster.Basic, zcl.Attribute.Manuf_Name) # Get Basic's Manufacturer Name
        if rprtg != None:
            pwrRpt = zcl.Cluster.PowerConfig+":"+zcl.Attribute.Batt_Percentage
            if zcl.Cluster.PowerConfig in inClstr and pwrRpt not in rprtg:
                pendingRptAttrId = zcl.Attribute.Batt_Percentage
                return ("AT+CFGRPT:"+devId+","+ep+",0,"+zcl.Cluster.PowerConfig+",0,"+zcl.Attribute.Batt_Percentage+",20,0E10,0E10,01", "CFGRPTRP")
            # Could add temperature reporting here, assuming binding already set up
        else:
            SetVal(devIdx, "Reporting", [])
    pendingAtCmd = GetTempVal(devIdx, "AtCmdRsp")
    if pendingAtCmd and consume:
        DelTempVal(devIdx,"AtCmdRsp") # Remove item if we're about to use it (presuming successful sending of command...)
    return pendingAtCmd

def SendPendingCommand():
    global info
    if telegesis.IsIdle() == True:
        devIdx = 0
        for device in info:
            for item in device:
                if IsListening(devIdx):# True if FFD, ZED or Polling
                    cmdRsp = Check(devIdx, True) # Automatically consume any pending command
                    if cmdRsp != None:
                        telegesis.TxCmd(cmdRsp)  # Send command directly
            devIdx = devIdx + 1

def IsListening(devIdx):
    type = GetVal(devIdx, "DevType")
    if type == "FFD" or type == "ZED":
        return True # These devices are always awake and listening
    else: # Assume sleepy (even if None), so check if we think it is polling
        pollTime = GetTempVal(devIdx, "PollingUntil")
        if pollTime != None:
            if datetime.now() < pollTime:
                log.log("Now: "+ str(datetime.now()))
                return True
        return False

def SwitchOn(devIdx, durationS):
    devId = GetVal(devIdx, "devId")
    ep = GetVal(devIdx, "EP")
    if devId and ep:
        telegesis.TxCmd(["AT+RONOFF:"+devId+","+ep+",0,1", "OK"]) # Assume FFD if it supports OnOff cluster
        if durationS>0: # Duration of 0 means "Stay on forever"
            SetTempVal(devIdx, "SwitchOff@", datetime.now()+timedelta(seconds=durationS))

def SwitchOff(devIdx):
    devId = GetVal(devIdx, "devId")
    ep = GetVal(devIdx, "EP")
    if devId and ep:
        DelTempVal(devIdx,"SwitchOff@") # Remove any pending "Off" events if we're turning the device off directly
        telegesis.TxCmd(["AT+RONOFF:"+devId+","+ep+",0,0", "OK"]) # Assume FFD if it supports OnOff cluster

def Toggle(devIdx):
    devId = GetVal(devIdx, "devId")
    ep = GetVal(devIdx, "EP")
    if devId and ep:
        DelTempVal(devIdx,"SwitchOff@") # Remove any pending "Off" events if we're handling the device directly
        telegesis.TxCmd(["AT+RONOFF:"+devId+","+ep+",0", "OK"]) # Assume FFD if it supports OnOff cluster

def FadeOn(devIdx, levelPercent, durationS):
    devId = GetVal(devIdx, "devId")
    ep = GetVal(devIdx, "EP")
    if devId and ep:
        levelStr = format((levelPercent * 2.55), 'X')
        telegesis.TxCmd(["AT+LCMVTOLEV:"+devId+","+ep+",0,0,"+levelStr+",0A00", "OK"]) # Fade over 1 sec (in 10ths)
        if durationS>0: # Duration of 0 means "Stay on forever"
            SetTempVal(devIdx, "SwitchOff@", datetime.now()+timedelta(seconds=durationS)) # Could be "FadeOff"

