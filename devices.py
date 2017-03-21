#!devices.py

from datetime import datetime
from datetime import timedelta
import time
#from pprint import pprint # Pretty print for devs list
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

globalDevIdx = None
pendingBinding = None # Needed because the BIND response doesn't include the cluster
pendingRptAttrId = None # Needed because CFGRPTRSP only includes the cluster and not the attr

# Keep a track of known devices present in the system
info = []
ephemera = [] # Don't bother saving this

def EventHandler(eventId, eventArg):
    global info, globalDevIdx, pendingBinding, pendingRptAttrId
    if eventId == events.ids.INIT:
        devIdx = 0
        numDevs = database.GetDevicesCount()
        for devs in range(0,numDevs):
            ephemera.append([]) # Initialise parallel ephemeral device list
            CopyDBToDev(devIdx)
            SetTempVal(devIdx, "LastSeen", datetime.now())  # Mark it as "seen at start up" so we don't start looking for it immediately
            devIdx = devIdx + 1
    if eventId == events.ids.DEVICE_ANNOUNCE:
        devId = eventArg[2]
        devIdx = GetIdx(devId)
        if devIdx == None:  # Which will only be the case if this device is actually new, but it may have just reset and announced
            devIdx = InitDev(devId)
            database.SetDeviceItem(devIdx, "Username", "(New) "+devId)   # Default username of network ID, since that's unique
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
    if eventId == events.ids.MINUTES:
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
    return database.GetDevIdx("nwkId", devId)

def CopyDBToDev(devIdx):
    InitDev(database.GetDeviceItem(devIdx, "nwkId"))
    SetVal(devIdx, "DevType", database.GetDeviceItem(devIdx, "devType"))
    SetVal(devIdx, "EUI", database.GetDeviceItem(devIdx, "eui64"))
    SetVal(devIdx, "devId", database.GetDeviceItem(devIdx, "nwkId"))
    SetVal(devIdx, "attr0000:0004", database.GetDeviceItem(devIdx, "manufName"))
    SetVal(devIdx, "attr0000:0005", database.GetDeviceItem(devIdx, "modelName"))
    SetVal(devIdx, "EP", database.GetDeviceItem(devIdx, "endPoints"))
    SetVal(devIdx, "InCluster", database.GetDeviceItem(devIdx, "inClusters"))
    SetVal(devIdx, "OutCluster", database.GetDeviceItem(devIdx, "outClusters"))

def InitDev(devId):
    global info
    log.log("Adding new devId: "+ str(devId))
    info.append([])  # If we didn't find it, then add empty device
    ephemera.append([]) # Add parallel ephemeral device list
    devIdx = len(info)-1 # -1 to convert number of elements in list to an index
    SetVal(devIdx,"devId",devId)
    return devIdx

def SetVal(devIdx, name, value):
    global info
    for item in info[devIdx]:
        if item[0] == name:
            info[devIdx].remove(item) # Remove old tuple if necessary
    info[devIdx].append((name, value)) # Add new one regardless
    
def GetVal(devIdx, name):
    global info
    for item in info[devIdx]:
        if item[0] == name:
            return item[1] # Just return value associated with name
    return None # Indicate item not found

def SetStatus(devIdx, name, value):# For web page
    if value != "N/A":
        database.NewEventUsingDevIdx(devIdx, name, value)

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

def SetVarFromAttr(devIdx, name, value): # See if this attribute has an associated variable for user & rules
    if name == "attr"+zcl.Cluster.PowerConfig+":"+zcl.Attribute.Batt_Percentage:
        SetTempVal(devIdx, "GetNextBatteryAfter", datetime.now()+timedelta(seconds=86400))    # Ask for battery every day
        if value != "FF":
            varVal = int(value, 16) / 2 # Arrives in 0.5% increments 
            SetStatus(devIdx, "Battery", str(varVal)) # For web page
        else:
            variables.Del(varName)
    if name == "attr"+zcl.Cluster.Temperature+":"+zcl.Attribute.Celsius:
        if value != "FF9C": # Don't know where this value comes from - should be "FFFF"
            varVal = int(value, 16) / 100 # Arrives in 0.01'C increments 
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
    if name == "attr"+zcl.Cluster.Basic+"."+zcl.Attribute.Manuf_Name or name == "attr"+zcl.Cluster.Basic+"."+zcl.Attribute.Model_Name:
        userName = database.GetDeviceItem(devIdx, "userName")
        if userName.find("(New)")==0:   # userName starts with "(New)"
            userName = userName + " " + value
            database.SetDeviceItem(devIdx, "userName", userName)

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

