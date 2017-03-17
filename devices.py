#!devices.py

from datetime import datetime
from datetime import timedelta
import time
from pprint import pprint # Pretty print for devs list
# App-specific modules
import events
import log
import hubapp
import telegesis
import rules
import variables
import zcl
import iottime
import database

if __name__ == "__main__":
    hubapp.main()

devFilename = "devices.txt"
devUserNames = "usernames.txt"
dirty = False
statusUpdate = False
globalDevIdx = None
pendingBinding = None # Needed because the BIND response doesn't include the cluster
pendingRptAttrId = None # Needed because CFGRPTRSP only includes the cluster and not the attr

# Keep a track of known devices present in the system
info = []
ephemera = [] # Don't bother saving this
synopsis = []
status = []

def EventHandler(eventId, eventArg):
    global info, dirty, globalDevIdx, pendingBinding, pendingRptAttrId, statusUpdate
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
        devIdx = 0
        database.ClearDevices()
        rowId = database.NewDevice("0000")
        database.UpdateDevice(rowId, "UserName", "Hub")
        database.UpdateDevice(rowId, "devType", "COO")
        database.UpdateDevice(rowId, "eui64", "")
        for devices in info:
            ephemera.append([]) # Initialise parallel ephemeral device list
            InitDevStatus(devIdx) # Initialise parallel device status
            CopyDevToDB(devIdx)
            SetTempVal(devIdx, "LastSeen", datetime.now())  # Mark it as "seen at start up" so we don't start looking for it immediately
            devIdx = devIdx + 1
        CheckAllAttrs() #  Set up any useful variables for the loaded devices
    if eventId == events.ids.DEVICE_ANNOUNCE:
        devId = eventArg[2]
        devIdx = GetIdx(devId)
        if devIdx == None:  # Which will only be the case if this device is actually new, but it may have just reset and announced
            devIdx = InitDev(devId)
            SetUserNameFromDevIdx(devIdx, "(New) "+devId)   # Default username of network ID, since that's unique
            SetVal(devIdx,"DevType",eventArg[0])    # SED, FFD or ZED
            SetVal(devIdx,"EUI",eventArg[1])
            if eventArg[0] == "SED":
                SetTempVal(devIdx,"PollingUntil", datetime.now()+timedelta(seconds=300))
        else:
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
                telegesis.TxCmd(["AT+RAWZCL:"+devId+","+endPoint+",0020,11"+seq+"00000100", "OK"]) # Tell device to stop Poll
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
    if eventId == events.ids.BUTTON:
        devIdx = GetIdx(eventArg[1]) # Lookup device from network address in eventArg[1]
        NoteEphemera(devIdx, eventArg)
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
        if statusUpdate:
            SaveStatus()
            statusUpdate = False
    if eventId == events.ids.MINUTES:
        SaveStatus()    # For app UpTime
        CheckPresence()   # For all devices
    # End event handler

def CheckPresence():  # Expected to be called infrequently - ie once/minute
    global info
    devIdx = 0
    for device in info:
        if GetTempVal(devIdx, "AtCmdRsp") == None:  # No pending command, so check whether device is present
            lastSeen = GetTempVal(devIdx, "LastSeen") 
            if lastSeen != None:
                if datetime.now() > lastSeen+timedelta(seconds=900): # More than 15 minutes since we last heard from device
                    devId = GetVal(devIdx, "devId")
                    ep = GetVal(devIdx, "EP")
                    if devId != None and ep != None:
                        pendingAtCmd = telegesis.ReadAttr(devId, ep, zcl.Cluster.Basic, zcl.Attribute.Model_Name) # Get Basic's Device Name
                        SetTempVal(devIdx, "AtCmdRsp", pendingAtCmd)
                if datetime.now() > lastSeen+timedelta(seconds=1800): # More than 30 minutes since we last heard from device
                    SetStatus(devIdx, "Presence", "* Missing *")
        devIdx = devIdx + 1

def GetIdx(devId):
    idx = GetIdxFromItem("devId", devId)
    if idx != None:
        return idx
    else:
        log.fault("Unknown device " + devId)
        return None 

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

def CopyDevToDB(devIdx):
    global info, dirty
    rowId = database.NewDevice(None)
    for item in info[devIdx]:
        if item[0] == "EUI":
            database.UpdateDevice(rowId, "eui64", item[1])
        if item[0] == "devId":
            database.UpdateDevice(rowId, "nwkId", item[1])
        if item[0] == "DevType":
            database.UpdateDevice(rowId, "devType", item[1])
        if item[0] == "attr0000:0004":
            database.UpdateDevice(rowId, "ManufName", item[1])
        if item[0] == "attr0000:0005":
            database.UpdateDevice(rowId, "ModelName", item[1])
        if item[0] == "EP":
            database.UpdateDevice(rowId, "endPoints", item[1])
        if item[0] == "InCluster":
            database.UpdateDevice(rowId, "inClusters", str(item[1]))
        if item[0] == "OutCluster":
            database.UpdateDevice(rowId, "outClusters", str(item[1]))
    name = GetUserNameFromDevIdx(devIdx)
    database.UpdateDevice(rowId, "UserName", name)

def SetUserNameFromDevIdx(devIdx, userName):
    with open(devUserNames, "r") as f:
        userNames = []
        for line in f:
            line = line.strip()
            userNames.append(line) # Load previous cache of device userNames into userNames
        f.close()
    if devIdx > len(userNames):
        userNames.append(userName)
    else:
        userNames[devIdx] = userName
    with open(devUserNames, "w") as f:
        for name in userNames:
            f.write(name+'\n')

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
    InitDevStatus(devIdx)
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

def InitDevStatus(devIdx):  # All devices have the same items
    global status
    status.append([])
    SetStatus(devIdx, "Battery", "N/A")
    SetStatus(devIdx, "Temperature", "N/A")
    SetStatus(devIdx, "Presence", "N/A")
    SetStatus(devIdx, "Other", "N/A")    

def SetStatus(devIdx, name, value):# For web page
    global status, statusUpdate
    for item in status[devIdx]:
        if item[0] == name:
            if item[1] == value:
                return  # Bail if value hasn't changed
            status[devIdx].remove(item) # Remove old tuple if value has changed
    status[devIdx].append((name, value)) # Add new one regardless
    if name == "Other" and value != "N/A":
        log.activity(devIdx, value)
    statusUpdate = True
    if value != "N/A":
        database.NewEventUsingDevIdx(devIdx, name, value)

def SaveStatus():
    global status
    devIdx = 0
    with open("status.xml", 'wt') as f:
        f.write("<status>\n");
        f.write("<hub>\n")
        upTime = datetime.now() - iottime.appStartTime
        f.write("<uptime>"+str(upTime).split('.', 2)[0]+"</uptime>\n")
        f.write("</hub>\n")
        for device in status:
            f.write("<device>\n");
            for item in status[devIdx]:
                f.write("<"+item[0]+">"+item[1]+"</"+item[0]+">\n");        
            f.write("</device>\n");
            devIdx = devIdx + 1
        f.write("</status>\n");
        f.close()
        
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
        #varName = GetUserNameFromDevIdx(devIdx)+"_BatteryPercentage"
        if value != "FF":
            varVal = int(value, 16) / 2 # Arrives in 0.5% increments 
            #variables.Set(varName, varVal)
            #SetSynopsis(varName, str(varVal)) # Ready for the synopsis email
            SetStatus(devIdx, "Battery", str(varVal)) # For web page
        else:
            variables.Del(varName)
    if name == "attr"+zcl.Cluster.Temperature+":"+zcl.Attribute.Celsius:
        #varName = GetUserNameFromDevIdx(devIdx)+"_TemperatureC"
        if value != "FF9C": # Don't know where this value comes from - should be "FFFF"
            varVal = int(value, 16) / 100 # Arrives in 0.01'C increments 
            #variables.Set(varName, varVal)
            SetStatus(devIdx, "Temperature", str(varVal)) # For web page
        else:
            variables.Del(varName)
    if name == "attr"+zcl.Cluster.OnOff+":"+zcl.Attribute.OnOffState:
        now = datetime.now()
        nowStr = now.strftime("%H:%M")
        varVal = int(value, 16)
        if varVal == 0:
            SetStatus(devIdx, "Other", "Turned Off")
        else:
            SetStatus(devIdx, "Other", "Turned On")
    if name == "attr"+zcl.Cluster.Basic+"."+zcl.Attribute.Manuf_Name:
        userName = GetUserNameFromDevIdx(devIdx)
        if userName.find("(New)")==0:
            userName = userName + " " + value
            SetUserNameFromDevIdx(devIdx, userName)
    if name == "attr"+zcl.Cluster.Basic+"."+zcl.Attribute.Model_Name:
        userName = GetUserNameFromDevIdx(devIdx)
        if userName.find("(New)")==0:
            userName = userName + " " + value
            SetUserNameFromDevIdx(devIdx, userName)

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
    SetTempVal(devIdx, "LastSeen", datetime.now())  # Mark it as "recently seen"
    SetStatus(devIdx, "Presence", "present") # For web page
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
        else:
            SetVal(devIdx, "Reporting", [])
    wantOnOff = GetTempVal(devIdx, "JustSentOnOff")
    if wantOnOff:
        DelTempVal(devIdx, "JustSentOnOff")
        return telegesis.ReadAttr(devId, ep, zcl.Cluster.OnOff, zcl.Attribute.OnOffState) # Get OnOff state after sending toggle
    pendingAtCmd = GetTempVal(devIdx, "AtCmdRsp")
    if pendingAtCmd:
        if consume:
            DelTempVal(devIdx,"AtCmdRsp") # Remove item if we're about to use it (presuming successful sending of command...)
    return pendingAtCmd

def SendPendingCommand():
    global info
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
                return True
        return False

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
        SetTempVal(devIdx, "JustSentOnOff", "True")
        telegesis.TxCmd(["AT+RONOFF:"+devId+","+ep+",0,1", "OK"]) # Assume FFD if it supports OnOff cluster

def SwitchOff(devIdx):
    devId = GetVal(devIdx, "devId")
    ep = GetVal(devIdx, "EP")
    if devId and ep:
        DelTempVal(devIdx,"SwitchOff@") # Remove any pending "Off" events if we're turning the device off directly
        telegesis.TxCmd(["AT+LCMVTOLEV:"+devId+","+ep+",0,0,FE,0001", "OK"]) # Ensure fully bright ready to be turned on later
        SetTempVal(devIdx, "JustSentOnOff", "True")
        telegesis.TxCmd(["AT+RONOFF:"+devId+","+ep+",0,0", "OK"]) # Assume FFD if it supports OnOff cluster

def Toggle(devIdx):
    devId = GetVal(devIdx, "devId")
    ep = GetVal(devIdx, "EP")
    if devId and ep:
        DelTempVal(devIdx,"SwitchOff@") # Remove any pending "Off" events if we're handling the device directly
        SetTempVal(devIdx, "JustSentOnOff", "True")
        telegesis.TxCmd(["AT+RONOFF:"+devId+","+ep+",0", "OK"]) # Assume FFD if it supports OnOff cluster

def Dim(devIdx, levelFraction):
    devId = GetVal(devIdx, "devId")
    ep = GetVal(devIdx, "EP")
    if devId and ep:
        levelStr = format(int(levelFraction * 254), 'X')
        telegesis.TxCmd(["AT+LCMVTOLEV:"+devId+","+ep+",0,1,"+levelStr+",000A", "OK"]) # Fade over 1 sec (in 10ths)

