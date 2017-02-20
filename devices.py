#!devices.py

from datetime import datetime
from datetime import timedelta
from pprint import pprint # Pretty print for devs list
# App-specific modules
import events
import log
import hubapp
import telegesis
import rules
import variables
import zcl

if __name__ == "__main__":
    hubapp.main()

devFilename = "devices.txt"
devUserNames = "usernames.txt"
dirty = False
globalDevIdx = None
pendingBinding = None # Needed because the BIND response doesn't include the cluster
pendingRptAttrId = None # Needed because CFGRPTRSP only includes the cluster and not the attr

# Keep a track of known devices present in the system
info = []
ephemera = [] # Don't bother saving this
synopsis = []

def EventHandler(eventId, eventArg):
    global info, dirty, globalDevIdx, pendingBinding, pendingRptAttrId
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
        for devices in info:
            ephemera.append([]) # Initialise parallel ephemeral device list
        CheckAllAttrs() #  Set up any useful variables for the loaded devices
    if eventId == events.ids.DEVICE_ANNOUNCE:
        devId = eventArg[2]
        devIdx = GetIdx(devId)
        if devIdx == None:  # Which will only be the case if this device is actually new, but it may have just reset and announced
            devIdx = InitDev(devId)
            SetVal(devIdx,"DevType",eventArg[0])    # SED, FFD or ZED
            SetVal(devIdx,"EUI",eventArg[1])
            NewUserName("New device "+devId)   # Default username of network ID, since that's unique
            if eventArg[0] == "SED":
                SetTempVal(devIdx,"PollingUntil", datetime.now()+timedelta(seconds=300))
        NoteEphemera(devIdx, eventArg)
    if eventId == events.ids.CHECKIN:   # See if we have anything to ask the device...
        endPoint = eventArg[2]
        seq = "00" # was seq = eventArg[3], but that's the RSSI
        devIdx = GetIdx(eventArg[1])
        if devIdx != None:
            NoteEphemera(devIdx, eventArg)
            if GetVal(devIdx, "EP") == None:
                SetVal(devIdx, "EP", endPoint) # Note endpoint that CheckIn came from, unless we already know this
            devId = GetVal(devIdx, "devId")
            cmdRsp = Check(devIdx, False)   # Check to see if we want to know anything about the device
            if cmdRsp != None:
                log.log("Want to know "+str(cmdRsp))
                telegesis.TxCmd(["AT+RAWZCL:"+devId+","+endPoint+",0020,11"+seq+"00012800", "OK"]) # Tell device to enter Fast Poll for 40qs (==10s)
                SetTempVal(devIdx,"PollingUntil", datetime.now()+timedelta(seconds=10))
                telegesis.TxCmd(cmdRsp)  # This will go out after the Fast Poll Set - but possibly ought to go out as part of SECONDS handler..?
            else:
                #log.log("Don't want to know anything about "+GetUserNameFromDevIdx(devIdx))
                telegesis.TxCmd(["AT+RAWZCL:"+devId+","+endPoint+",0020,11"+seq+"0000", "OK"]) # Tell device to stop Poll
    if eventId == events.ids.RXMSG:
        if eventArg[0] == "AddrResp" and eventArg[1] == "00":
            devIdx = GetIdx(eventArg[2])
            if devIdx != None:
                SetVal(devIdx,"EUI",eventArg[3])
        elif eventArg[0] == "ActEpDesc":
            if "00" == eventArg[2]:
                devIdx = GetIdx(eventArg[1])
                if devIdx != None:
                    SetVal(devIdx, "EP", eventArg[3]) # Note first endpoint
        elif eventArg[0] == "SimpleDesc":
            if "00" == eventArg[2]:
                globalDevIdx = GetIdx(eventArg[1]) # Is multi-line response, so expect rest of response and use this global index until it's all finished
            elif "82" == eventArg[2]:   # 82 == Invalid endpoint
                devIdx = GetIdx(eventArg[1])
                DelVal(devIdx, "EP")
                events.Issue(events.ids.RXERROR, int(eventArg[2],16)) # Tell system that we're aborting this command
        elif eventArg[0] == "InCluster":
           if globalDevIdx != None:
             SetVal(globalDevIdx, "InCluster", eventArg[1:]) # Store whole list from arg[1] to arg[n]
        elif eventArg[0] == "OutCluster":
            if globalDevIdx != None:
                NoteEphemera(globalDevIdx, eventArg)
                SetVal(globalDevIdx, "OutCluster", eventArg[1:]) # Store whole list from arg[1] to arg[n]
            globalDevIdx = None # We've finished with this global for now
        if eventArg[0] == "RESPATTR":
            devIdx = GetIdx(eventArg[1])
            if devIdx != None:
                NoteEphemera(devIdx, eventArg)
                ep = eventArg[2]
                clusterId = eventArg[3]
                attrId = eventArg[4]
                if "00" == eventArg[5]:
                    attrVal = eventArg[6]
                else:
                    attrVal = "Error:"+eventArg[5]   # So that we don't ask for the same attribute again later
                SetAttrVal(devIdx, clusterId, attrId, attrVal)
        if eventArg[0] == "REPORTATTR":
            devIdx = GetIdx(eventArg[1])
            if devIdx != None:
                ep = eventArg[2]
                clusterId = eventArg[3]
                attrId = eventArg[4]
                attrType = eventArg[5]
                attrVal = eventArg[6]
                NoteEphemera(devIdx, eventArg)
                SetAttrVal(devIdx, clusterId, attrId, attrVal)
                reporting = GetVal(devIdx, "Reporting") # See if we're expecting this report, and note it in the reporting table
                if reporting != None:
                    newRpt = clusterId+":"+attrId
                    if newRpt not in reporting:
                        reporting.append(newRpt)
                        SetVal(devIdx, "Reporting", reporting)
                else:
                    SetVal(devIdx, "Reporting", []) # Ready for next time
        if eventArg[0] == "Bind":    # Binding Response from device
            devIdx = GetIdx(eventArg[1])
            if devIdx != None:
                if pendingBinding != None:
                    binding = GetVal(devIdx, "Binding")
                    binding.append(pendingBinding)
                    SetVal(devIdx, "Binding", binding)
                    pendingBinding = None
        if eventArg[0] == "CFGRPTRSP":   # Configure Report Response from device
            devIdx = GetIdx(eventArg[1])
            status = eventArg[4]
            if devIdx != None and status == "00":
                clusterId = eventArg[3]
                attrId = pendingRptAttrId # Need to remember this, since it doesn't appear in CFGRPTRSP
                reporting = GetVal(devIdx, "Reporting")
                newRpt = clusterId+":"+attrId
                if newRpt not in reporting:
                    reporting.append(newRpt)
                    SetVal(devIdx, "Reporting", reporting)
    if eventId == events.ids.RXERROR:
        globalDevIdx = None # We've finished with this global if we get an error
    if eventId == events.ids.SECONDS:
        SendPendingCommand()
        for devIdx, devInfo in enumerate(info):  # See if any devices are timing out, and turn them off if necessary
            offAt = GetVal(devIdx, "SwitchOff@")
            if offAt:
                if now >= offAt:
                    SwitchOff(devIdx)
        if dirty:
            with open(devFilename, 'wt') as f:
                pprint(info, stream=f)
                # Was print(info, file=f) # Save devices list directly to file
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

def NewUserName(name):
    with open(devUserNames, "a") as f:
        try:
            f.append(name+"\n")
            return
        except:
            log.fault("No usernames!")
    return None # Item not found    

def SetUserNameFromDevIdx(devIdx, userName):
    with open(devUserNames, "r") as f:
        userNames = []
        for line in f:
            line = line.strip()
            userNames.append(line) # Load previous cache of device userNames into userNames
        userNames[devIdx] = userName
        # Ought to write it back out to disk here...

def GetDevIdxFromUserName(userName):
    with open(devUserNames, "r") as f:
        userNames = []
        for line in f:
            line = line.strip()
            userNames.append(line) # Load previous cache of device userNames into userNames
        try:
            return userNames.index(userName)
        except ValueError:
            return None # Item not found
    return None # Item not found    

def GetUserNameFromDevIdx(devIdx):
    with open(devUserNames, "r") as f:
        userNames = []
        for line in f:
            line = line.strip()
            userNames.append(line) # Load previous cache of device userNames into userNames
        try:
            return userNames[devIdx]
        except:
            return None # Item not found, if index is outside list
    return None # Item not found

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
    
def SetSynopsis(name, value): # Ready for the synopsis email
    global synopsis
    for item in synopsis:
        if item[0] == name:
            synopsis.remove(item) # Remove old tuple if necessary
    synopsis.append((name, value)) # Add new one regardless

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
    SetVarFromAttr(devIdx, name, value)

def CheckAllAttrs():
    global info
    devIdx = 0
    for device in info:
        for item in device:
            if "attr" in item[0]:
                SetVarFromAttr(devIdx, item[0], item[1])
        devIdx = devIdx + 1
    
def SetVarFromAttr(devIdx, name, value): # See if this attribute has an associated variable for user & rules
    if name == "attr"+zcl.Cluster.PowerConfig+":"+zcl.Attribute.Batt_Percentage:
        SetTempVal(devIdx, "GetNextBatteryAfter", datetime.now()+timedelta(seconds=86400))    # Ask for battery every day
        varName = GetUserNameFromDevIdx(devIdx)+"_BatteryPercentage"
        if value != "FF":
            varVal = int(value, 16) / 2 # Arrives in 0.5% increments 
            variables.Set(varName, varVal)
            SetSynopsis(varName, str(varVal)) # Ready for the synopsis email
        else:
            variables.Del(varName)
    if name == "attr"+zcl.Cluster.Temperature+":"+zcl.Attribute.Celsius:
        varName = GetUserNameFromDevIdx(devIdx)+"_TemperatureC"
        if value != "FF9C": # Don't know where this value comes from - should be "FFFF"
            varVal = int(value, 16) / 100 # Arrives in 0.01'C increments 
            variables.Set(varName, varVal)
        else:
            variables.Del(varName)

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
    variables.Set(GetUserNameFromDevIdx(devIdx)+"_LastSeen", datetime.now().strftime("%y/%m/%d %H:%M:%S"))  # Mark it as "recently seen"
    DelTempVal(devIdx, "ReportedMissing") # ToDo Could only remove this once per day? to avoid spamming
    SetTempVal(devIdx, "LastSeen", datetime.now())  # Mark it as "recently seen"
    SetTempVal(devIdx, "ReportMissingAfter", datetime.now()+timedelta(seconds=1800))
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
    eui = GetVal(devIdx, "EUI")
    if None == ep:
        return ("AT+ACTEPDESC:"+devId+","+devId, "ActEpDesc")
    if None == eui:
        return ("AT+EUIREQ:"+devId+","+devId, "AddrResp")
    if None == GetVal(devIdx, "InCluster") or None == GetVal(devIdx, "OutCluster"):
        SetVal(devIdx, "OutCluster", []) # Some devices have no outclusters...
        return ("AT+SIMPLEDESC:"+devId+","+devId+","+ep, "OutCluster")
    inClstr = GetVal(devIdx, "InCluster") # Assume we have a list of clusters if we get this far
    outClstr = GetVal(devIdx, "OutCluster")
    binding = GetVal(devIdx, "Binding")
    rprtg = GetVal(devIdx, "Reporting")
    if inClstr != None:
        if binding != None:
            if zcl.Cluster.PollCtrl in inClstr and zcl.Cluster.PollCtrl not in binding:
                return SetBinding(devIdx, zcl.Cluster.PollCtrl, "01") # 01 is our endpoint we want messages to come to
            if zcl.Cluster.OnOff in outClstr and zcl.Cluster.OnOff not in binding: # If device sends OnOff commands...
                return SetBinding(devIdx, zcl.Cluster.OnOff, "0A") # 0A is our endpoint we want messages to come to
            if zcl.Cluster.Temperature in inClstr and zcl.Cluster.Temperature not in binding:
                return SetBinding(devIdx, zcl.Cluster.Temperature, "01") # 01 is our endpoint we want messages to come to
        else:
            SetVal(devIdx, "Binding", [])
        if zcl.Cluster.IAS_Zone in inClstr:
            if None == GetAttrVal(devIdx, zcl.Cluster.IAS_Zone, zcl.Attribute.Zone_Type):
                return telegesis.ReadAttr(devId, ep, zcl.Cluster.IAS_Zone, zcl.Attribute.Zone_Type) # Get IAS device type (PIR or contact, etc.)
        if zcl.Cluster.Basic in inClstr:
            if None == GetAttrVal(devIdx, zcl.Cluster.Basic, zcl.Attribute.Model_Name):
                return telegesis.ReadAttr(devId, ep, zcl.Cluster.Basic, zcl.Attribute.Model_Name) # Get Basic's Device Name
            if None == GetAttrVal(devIdx, zcl.Cluster.Basic, zcl.Attribute.Manuf_Name):
                return telegesis.ReadAttr(devId, ep, zcl.Cluster.Basic, zcl.Attribute.Manuf_Name) # Get Basic's Manufacturer Name
        if zcl.Cluster.PowerConfig in inClstr and "SED"== GetVal(devIdx, "DevType"):
            if None == GetAttrVal(devIdx, zcl.Cluster.PowerConfig, zcl.Attribute.Batt_Percentage) or datetime.now() > GetTempVal(devIdx, "GetNextBatteryAfter"):
                return telegesis.ReadAttr(devId, ep, zcl.Cluster.PowerConfig, zcl.Attribute.Batt_Percentage) # Get Battery percentage
        if rprtg != None:
            if zcl.Cluster.Temperature in inClstr:
                tmpRpt = zcl.Cluster.Temperature+":"+zcl.Attribute.Celsius
                if zcl.Cluster.Temperature in binding and tmpRpt not in rprtg:
                    pendingRptAttrId = zcl.Attribute.Celsius
                    return ("AT+CFGRPT:"+devId+","+ep+",0,"+zcl.Cluster.Temperature+",0,"+zcl.Attribute.Celsius+","+zcl.AttributeTypes.Uint16+",012C,0E10,0064", "CFGRPTRP") # 012C is 300==5 mins, 0E10 is 3600==1 hour, 0064 is 100, being 1.00'C
#            if zcl.Cluster.OnOff in inClstr: # Commented out because TG won't let me set up reports for booleans
#                onOffRpt = zcl.Cluster.OnOff+":"+zcl.Attribute.OnOffState
#                if zcl.Cluster.OnOff in binding and onOffRpt not in rprtg:
#                    pendingRptAttrId = zcl.Attribute.OnOffState
#                    return ("AT+CFGRPT:"+devId+","+ep+",0,"+zcl.Cluster.OnOff+",0,"+zcl.Attribute.OnOffState+","+zcl.AttributeTypes.Boolean+",0005,0E10,01", "CFGRPTRP") # 0E10 is 3600==1 hour, 01 is "reportable change"
        else:
            SetVal(devIdx, "Reporting", [])
    pendingAtCmd = GetTempVal(devIdx, "AtCmdRsp")
    if pendingAtCmd:
        if consume:
            DelTempVal(devIdx,"AtCmdRsp") # Remove item if we're about to use it (presuming successful sending of command...)
    else: # No pending command, so check whether device has said anything for a while...
        if GetTempVal(devIdx, "LastSeen") != None:
            if GetTempVal(devIdx, "LastSeen")+timedelta(seconds=900) < datetime.now(): # 15 minutes since we last heard from device 
                if zcl.Cluster.Basic in inClstr: # Ask for Basic's Name, since everything must support this
                    pendingAtCmd = telegesis.ReadAttr(devId, ep, zcl.Cluster.Basic, zcl.Attribute.Model_Name) # Get Basic's Device Name
    return pendingAtCmd

def SendPendingCommand():
    global info
    if telegesis.IsIdle() == True:
        devIdx = 0
        for device in info:
            if IsListening(devIdx):# True if FFD, ZED or Polling
                offTime = GetTempVal(devIdx, "SwitchOff@")
                if offTime != None:
                    if datetime.now() > offTime:
                        SwitchOff(devIdx)
                cmdRsp = Check(devIdx, True) # Automatically consume any pending command
                if cmdRsp != None:
                    log.log("Sending "+str(cmdRsp))
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
                #log.log("Now: "+ str(datetime.now()))
                return True
        return False

def CheckMissing():
    global info
    devIdx = 0
    for device in info:
        if GetTempVal(devIdx, "ReportedMissing") == None:
            if GetTempVal(devIdx, "ReportMissingAfter") != None:
                if GetTempVal(devIdx, "ReportMissingAfter") > timedate.now(): # 30 minutes
                    variables.Set("MissingDevice", GetUserNameFromDevIdx(devIdx))
                    rules.Run("Missing==True") # Trigger is "missing"
                    SetTempVal(devIdx, "ReportedMissing", timedate.now())   # To avoid re-reporting
        devIdx = devIdx + 1

def SetBinding(devIdx, cluster, ourEp):
    global pendingBinding
    devId = GetVal(devIdx, "devId")
    ep = GetVal(devIdx, "EP")
    eui = GetVal(devIdx, "EUI")
    if None != ep and None != eui: 
        pendingBinding = cluster
        return ("AT+BIND:"+devId+",3,"+eui+","+ep+","+cluster+","+telegesis.ourEui+","+ourEp, "Bind")

def SwitchOn(devIdx):
    devId = GetVal(devIdx, "devId")
    ep = GetVal(devIdx, "EP")
    if devId and ep:
        telegesis.TxCmd(["AT+RONOFF:"+devId+","+ep+",0,1", "OK"]) # Assume FFD if it supports OnOff cluster

def SwitchOff(devIdx):
    devId = GetVal(devIdx, "devId")
    ep = GetVal(devIdx, "EP")
    if devId and ep:
        DelTempVal(devIdx,"SwitchOff@") # Remove any pending "Off" events if we're turning the device off directly
        telegesis.TxCmd(["AT+LCMVTOLEV:"+devId+","+ep+",0,0,FE,0001", "OK"]) # Ensure fully bright ready to be turned on later
        telegesis.TxCmd(["AT+RONOFF:"+devId+","+ep+",0,0", "OK"]) # Assume FFD if it supports OnOff cluster

def Toggle(devIdx):
    devId = GetVal(devIdx, "devId")
    ep = GetVal(devIdx, "EP")
    if devId and ep:
        DelTempVal(devIdx,"SwitchOff@") # Remove any pending "Off" events if we're handling the device directly
        telegesis.TxCmd(["AT+RONOFF:"+devId+","+ep+",0", "OK"]) # Assume FFD if it supports OnOff cluster

def Dim(devIdx, levelFraction):
    devId = GetVal(devIdx, "devId")
    ep = GetVal(devIdx, "EP")
    if devId and ep:
        levelStr = format(int(levelFraction * 254), 'X')
        telegesis.TxCmd(["AT+LCMVTOLEV:"+devId+","+ep+",0,1,"+levelStr+",000A", "OK"]) # Fade over 1 sec (in 10ths)

