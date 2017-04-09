#!devices.py

from datetime import datetime
from datetime import timedelta
import time
from array import *
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
import presence

globalDevIdx = None
pendingBinding = None # Needed because the BIND response doesn't include the cluster
pendingRptAttrId = None # Needed because CFGRPTRSP only includes the cluster and not the attr

# Keep a track of known devices present in the system
ephemera = [] # Don't bother saving this
txQueue = [] # Queue of outbound messages & responses for each device
expRsp = [] # List of expected responses for each device
expRspTimeoutS = array('f',[]) # Array of timeouts if we're expecting a response, one per device

def EventHandler(eventId, eventArg):
    global ephemera, globalDevIdx, pendingBinding, pendingRptAttrId
    if eventId == events.ids.PREINIT:
        numDevs = database.GetDevicesCount()
        for devIdx in range(0, numDevs):  # Element 0 is hub, rest are devices
            database.InitStatus(devIdx)
            ephemera.append([]) # Initialise parallel ephemeral device list
            InitQueue(devIdx) # Initial empty output queue per device
            if devIdx > 0:
                presence.Set(devIdx, presence.states.unknown)
                SetTempVal(devIdx, "GetNextBatteryAfter", datetime.now())    # Ask for battery shortly after startup
    if eventId == events.ids.DEVICE_ANNOUNCE:
        devId = eventArg[2]
        devIdx = GetIdx(devId)
        if devIdx == None:  # Which will only be the case if this device is actually new, but it may have just reset and announced
            devIdx = InitDev()
            database.SetDeviceItem(devIdx, "nwkId", devId)
            database.SetDeviceItem(devIdx, "Username", "(New) "+devId)   # Default username of network ID, since that's unique
            database.SetDeviceItem(devIdx,"devType",eventArg[0])    # SED, FFD or ZED
            database.SetDeviceItem(devIdx,"eui64",eventArg[1])
            if eventArg[0] == "SED":
                SetTempVal(devIdx,"PollingUntil", datetime.now()+timedelta(seconds=300))
        else:
            NoteMsgDetails(devIdx, eventArg)
    if eventId == events.ids.CHECKIN:   # See if we have anything to ask the device...
        endPoint = eventArg[2]
        seq = "00" # was seq = eventArg[3], but that's the RSSI
        devIdx = GetIdx(eventArg[1])
        if devIdx != None:
            NoteMsgDetails(devIdx, eventArg)
            if database.GetDeviceItem(devIdx, "endPoints") == None:
                database.SetDeviceItem(devIdx, "endPoints", endPoint) # Note endpoint that CheckIn came from, unless we already know this
            devId = database.GetDeviceItem(devIdx, "nwkId")
            cmdRsp = Check(devIdx)   # Check to see if we want to know anything about the device
            if cmdRsp != None:
                log.debug("Want to know "+str(cmdRsp))
                JumpQueueCmd(devIdx, ["AT+RAWZCL:"+devId+","+endPoint+",0020,11"+seq+"00012800", "DFTREP"]) # Tell device to enter Fast Poll for 40qs (==10s)
                SetTempVal(devIdx,"PollingUntil", datetime.now()+timedelta(seconds=10))
                EnqueueCmd(devIdx, cmdRsp)  # This will go out after the Fast Poll Set
            else:
                EnqueueCmd(devIdx, ["AT+RAWZCL:"+devId+","+endPoint+",0020,11"+seq+"00000100", "DFTREP"]) # Tell device to stop Poll
    if eventId == events.ids.RXMSG:
        if eventArg[0] == "AddrResp" and eventArg[1] == "00":
            devIdx = GetIdx(eventArg[2])
            if devIdx != None:
                database.SetDeviceItem(devIdx,"eui64",eventArg[1])
        elif eventArg[0] == "ActEpDesc":
            if "00" == eventArg[2]:
                devIdx = GetIdx(eventArg[1])
                if devIdx != None:
                    database.SetDeviceItem(devIdx, "endPoints", eventArg[3]) # Note first endpoint
        elif eventArg[0] == "SimpleDesc":
            if "00" == eventArg[2]:
                globalDevIdx = GetIdx(eventArg[1]) # Is multi-line response, so expect rest of response and use this global index until it's all finished
            elif "82" == eventArg[2]:   # 82 == Invalid endpoint
                devIdx = GetIdx(eventArg[1])
                events.Issue(events.ids.RXERROR, int(eventArg[2],16)) # Tell system that we're aborting this command
        elif eventArg[0] == "InCluster":
            if globalDevIdx != None:
                database.SetDeviceItem(globalDevIdx, "inClusters", str(eventArg[1:])) # Store whole list from arg[1] to arg[n]
        elif eventArg[0] == "OutCluster":
            if globalDevIdx != None:
                NoteMsgDetails(globalDevIdx, eventArg)
                database.SetDeviceItem(globalDevIdx, "outClusters", str(eventArg[1:])) # Store whole list from arg[1] to arg[n]
            globalDevIdx = None # We've finished with this global for now
        elif eventArg[0] == "RESPATTR":
            devIdx = GetIdx(eventArg[1])
            if devIdx != None:
                NoteMsgDetails(devIdx, eventArg)
                ep = eventArg[2]
                clusterId = eventArg[3]
                attrId = eventArg[4]
                if "00" == eventArg[5]:
                    attrVal = eventArg[6]
                    SetAttrVal(devIdx, clusterId, attrId, attrVal)
        elif eventArg[0] == "REPORTATTR":
            devIdx = GetIdx(eventArg[1])
            if devIdx != None:
                ep = eventArg[2]
                clusterId = eventArg[3]
                attrId = eventArg[4]
                attrType = eventArg[5]
                attrVal = eventArg[6]
                NoteMsgDetails(devIdx, eventArg)
                SetAttrVal(devIdx, clusterId, attrId, attrVal)
                NoteReporting(devIdx, clusterId, attrId)
        elif eventArg[0] == "Bind":    # Binding Response from device
            devIdx = GetIdx(eventArg[1])
            if devIdx != None:
                if pendingBinding != None:
                    binding = eval(database.GetDeviceItem(devIdx, "binding"))
                    if pendingBinding not in binding:   # Only put it in once, even if we get multiple responses
                        binding.append(pendingBinding)
                        database.SetDeviceItem(devIdx, "binding", str(binding))
                    pendingBinding = None
        elif eventArg[0] == "CFGRPTRSP":   # Configure Report Response from device
            devIdx = GetIdx(eventArg[1])
            status = eventArg[4]
            if devIdx != None and status == "00":
                clusterId = eventArg[3]
                attrId = pendingRptAttrId # Need to remember this, since it doesn't appear in CFGRPTRSP
                NoteReporting(devIdx, clusterId, attrId)
        else:   # Unrecognised message, but we still want to extract OOB info
            if len(eventArg) >= 2:
                devIdx = GetIdx(eventArg[1])    # Assume this is sensible
                if devIdx != None:
                    NoteMsgDetails(devIdx, eventArg)
    if eventId == events.ids.BUTTON:
        devIdx = GetIdx(eventArg[1]) # Lookup device from network address in eventArg[1]
        NoteMsgDetails(devIdx, eventArg)
    if eventId == events.ids.RXERROR:
        globalDevIdx = None # We've finished with this global if we get an error
    if eventId == events.ids.SECONDS:
        numDevs = database.GetDevicesCount()
        for devIdx in range(0, numDevs):  # Element 0 is hub, but this can have messages too, so use it
            if IsListening(devIdx):  # True if FFD, ZED or Polling
                if expRsp[devIdx] == None:  # We don't have a message in flight
                    cr = Check(devIdx)
                    if cr:
                        EnqueueCmd(devIdx, cr)   # Queue up anything we ought to know
                    cmdRsp = DequeueCmd(devIdx) # Pull first item from queue
                    if cmdRsp != None:
                        log.debug("Sending "+str(cmdRsp))
                        expRsp[devIdx] = cmdRsp[1]  # Note response
                        expRspTimeoutS[devIdx] = 2  # If we've not heard back after 2 seconds, it's probably got lost, so try again
                        telegesis.TxCmd(cmdRsp[0])  # Send command directly
                else:   # We're expecting a response, so time it out
                    expRspTimeoutS[devIdx] = expRspTimeoutS[devIdx] - eventArg
                    if expRspTimeoutS[devIdx] <= 0:
                        expRsp[devIdx] = None
            offAt = GetTempVal(devIdx, "SwitchOff@")
            if offAt:
                if datetime.now() >= offAt:
                    SwitchOff(devIdx)
            pirOffAt = GetTempVal(devIdx, "PirInactive@")
            if pirOffAt:
                if datetime.now() >= pirOffAt:
                    DelTempVal(devIdx, "PirInactive@")
                    newState = "inactive"
                    database.NewEvent(devIdx, newState)
                    Rule(devIdx, newState)
    if eventId == events.ids.MINUTES:
        presence.Check()   # For all devices
    # End event handler

def NoteReporting(devIdx, clusterId, attrId):
    reporting = database.GetDeviceItem(devIdx, "reporting") # See if we're expecting this report, and note it in the reporting table
    newRpt = clusterId+":"+attrId
    if reporting != None:
        reportList = eval(reporting)
        if newRpt not in reportList:
            reportList.append(newRpt)
            reporting = str(reportList)
    else:
        reporting = "['"+newRpt+"']"
    print ("Reporting = "+reporting)
    database.SetDeviceItem(devIdx, "reporting", reporting) # Ready for next time

def GetIdx(devId):
    return database.GetDevIdx("nwkId", devId)

def FindDev(devId):
    devIdx = database.GetDevIdx("userName", devId) # Try name first
    if devIdx:
        return devIdx
    return devices.GetIdx(devId)   # Try devId if no name match

def InitDev():
    #log.debug("Adding new devId: "+ str(devId))
    ephemera.append([]) # Add parallel ephemeral device list
    devIdx = database.NewDevice()
    InitQueue(devIdx)
    return devIdx

def SetAttrVal(devIdx, clstrId, attrId, value):
    if clstrId == zcl.Cluster.PowerConfig and attrId == zcl.Attribute.Batt_Percentage:
        SetTempVal(devIdx, "GetNextBatteryAfter", datetime.now()+timedelta(seconds=86400))    # Ask for battery every day
        if value != "FF":
            varVal = int(int(value, 16) / 2) # Arrives in 0.5% increments, but drop fractional component
            database.SetStatus(devIdx, "battery", varVal) # For web page
        else:
            variables.Del(varName)
    if clstrId == zcl.Cluster.Temperature and attrId == zcl.Attribute.Celsius:
        if value != "FF9C": # Don't know where this value comes from - should be "FFFF"
            varVal = int(value, 16) / 100 # Arrives in 0.01'C increments 
            database.SetStatus(devIdx, "temperature", varVal) # For web page
        else:
            variables.Del(varName)
    if clstrId == zcl.Cluster.OnOff and attrId == zcl.Attribute.OnOffState:
        oldState = database.GetLatestEvent(devIdx)
        if int(value, 16) == 0:
            newState = "SwitchedOff"
        else:
            newState = "SwitchedOn"
        if oldState != newState:
            database.NewEvent(devIdx, newState)
            Rule(devIdx, newState)
    if clstrId == zcl.Cluster.SimpleMetering and attrId == zcl.Attribute.InstantaneousDemand:
        varVal = int(value, 16) # Arrives in Watts, so store it in the same way
        database.SetDeviceItem(devIdx, "powerReading", varVal)
    if clstrId == zcl.Cluster.IAS_Zone and attrId == zcl.Attribute.Zone_Type:
        database.SetDeviceItem(devIdx, "iasZoneType", value)
    if clstrId == zcl.Cluster.Basic:
        if attrId == zcl.Attribute.Model_Name:
            database.SetDeviceItem(devIdx, "modelName", value)
        if attrId == zcl.Attribute.Manuf_Name:
            database.SetDeviceItem(devIdx, "manufName", value)

def Rule(devIdx, state):
    rules.Run(database.GetDeviceItem(devIdx, "userName")+"=="+state)

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

def NoteMsgDetails(devIdx, arg):
    if arg[0] == expRsp[devIdx]:
        expRsp[devIdx] = None   # Note that we've found the expected response now, so we're now clear to send
    presence.Set(devIdx, presence.states.present) # Note presence
    if isnumeric(arg[-2]):
        if int(arg[-2]) < 0: # Assume penultimate item is RSSI, and thus that ultimate one is LQI
            rssi = arg[-2]
            lqi = arg[-1]
            signal = int((int(lqi, 16) * 100) / 255)    # Convert 0-255 to 0-100.  Ignore RSSI for now
            database.SetStatus(devIdx, "signal", signal)
            arg.remove(rssi)
            arg.remove(lqi)

def isnumeric(item):
    try:
        val = int(item)
        return True
    except ValueError:
        return False

def Check(devIdx):
    global pendingBinding, pendingRptAttrId
    if devIdx == 0:
        return  # We don't need anything from the hub
    devId = database.GetDeviceItem(devIdx, "nwkId")
    ep = database.GetDeviceItem(devIdx, "endPoints")
    eui = database.GetDeviceItem(devIdx, "eui64")
    inClstr = database.GetDeviceItem(devIdx, "inClusters") # Assume we have a list of clusters if we get this far
    outClstr = database.GetDeviceItem(devIdx, "outClusters")
    if None == ep:
        return ("AT+ACTEPDESC:"+devId+","+devId, "ActEpDesc")
    if None == eui:
        return ("AT+EUIREQ:"+devId+","+devId, "AddrResp")
    if None == inClstr or None == outClstr:
        database.SetDeviceItem(devIdx, "outClusters", "[]") # Some devices have no outclusters...
        return ("AT+SIMPLEDESC:"+devId+","+devId+","+ep, "OutCluster")
    binding = database.GetDeviceItem(devIdx, "binding")
    rprtg = database.GetDeviceItem(devIdx, "reporting")
    if inClstr != None:
        if binding != None and pendingBinding == None:  # Only try to add one binding at once
            if zcl.Cluster.PollCtrl in inClstr and zcl.Cluster.PollCtrl not in binding:
                return SetBinding(devIdx, zcl.Cluster.PollCtrl, "01") # 01 is our endpoint we want messages to come to
            if zcl.Cluster.OnOff in outClstr and zcl.Cluster.OnOff not in binding: # If device sends OnOff commands...
                return SetBinding(devIdx, zcl.Cluster.OnOff, "0A") # 0A is our endpoint we want messages to come to (so that we get TOGGLE, ON and OFF commands)
            if zcl.Cluster.Temperature in inClstr and zcl.Cluster.Temperature not in binding:
                return SetBinding(devIdx, zcl.Cluster.Temperature, "01") # 01 is our endpoint we want messages to come to
            if zcl.Cluster.SimpleMetering in inClstr and zcl.Cluster.SimpleMetering not in binding:
                return SetBinding(devIdx, zcl.Cluster.SimpleMetering, "01") # 01 is our endpoint we want messages to come to
        else:
            database.SetDeviceItem(devIdx, "binding", "[]")
        if zcl.Cluster.IAS_Zone in inClstr:
            if None == database.GetDeviceItem(devIdx, "iasZoneType"):
                return telegesis.ReadAttr(devId, ep, zcl.Cluster.IAS_Zone, zcl.Attribute.Zone_Type) # Get IAS device type (PIR or contact, etc.)
        if zcl.Cluster.Basic in inClstr:
            if None == database.GetDeviceItem(devIdx, "modelName"):
                return telegesis.ReadAttr(devId, ep, zcl.Cluster.Basic, zcl.Attribute.Model_Name) # Get Basic's Device Name
            if None == database.GetDeviceItem(devIdx, "manufName"):
                return telegesis.ReadAttr(devId, ep, zcl.Cluster.Basic, zcl.Attribute.Manuf_Name) # Get Basic's Manufacturer Name
        if zcl.Cluster.PowerConfig in inClstr and "SED"== database.GetDeviceItem(devIdx, "devType"):
            checkBatt = GetTempVal(devIdx, "GetNextBatteryAfter")
            if checkBatt != None:
                if datetime.now() > checkBatt:
                    return telegesis.ReadAttr(devId, ep, zcl.Cluster.PowerConfig, zcl.Attribute.Batt_Percentage) # Get Battery percentage
        if rprtg != None:
            if zcl.Cluster.Temperature in inClstr:
                tmpRpt = zcl.Cluster.Temperature+":"+zcl.Attribute.Celsius
                if zcl.Cluster.Temperature in binding and tmpRpt not in rprtg:
                    pendingRptAttrId = zcl.Attribute.Celsius
                    return ("AT+CFGRPT:"+devId+","+ep+",0,"+zcl.Cluster.Temperature+",0,"+zcl.Attribute.Celsius+","+zcl.AttributeTypes.Uint16+",012C,0E10,0064", "CFGRPTRSP") # 012C is 300==5 mins, 0E10 is 3600==1 hour, 0064 is 100, being 1.00'C
            if zcl.Cluster.SimpleMetering in inClstr:
                tmpRpt = zcl.Cluster.SimpleMetering+":"+zcl.Attribute.InstantaneousDemand
                if zcl.Cluster.SimpleMetering in binding and tmpRpt not in rprtg:
                    pendingRptAttrId = zcl.Attribute.InstantaneousDemand
                    return ("AT+CFGRPT:"+devId+","+ep+",0,"+zcl.Cluster.SimpleMetering+",0,"+zcl.Attribute.InstantaneousDemand+","+zcl.AttributeTypes.Sint24+",0005,003C,00000A", "CFGRPTRSP") # 5 second minimum, 1 minute maximum, 10 watt change
        else:
            database.SetDeviceItem(devIdx, "reporting", "[]")
    if GetTempVal(devIdx, "JustSentOnOff"):
        DelTempVal(devIdx, "JustSentOnOff")
        return telegesis.ReadAttr(devId, ep, zcl.Cluster.OnOff, zcl.Attribute.OnOffState) # Get OnOff state after sending toggle
    return None

def IsListening(devIdx):
    type = database.GetDeviceItem(devIdx, "devType")
    if type == "SED":
        pollTime = GetTempVal(devIdx, "PollingUntil")
        if pollTime != None:
            if datetime.now() < pollTime:
                return True
        return False
    else: # Assume not sleepy
        return True # These devices are always awake and listening

def SetBinding(devIdx, cluster, ourEp):
    global pendingBinding
    devId = database.GetDeviceItem(devIdx, "nwkId")
    ep = database.GetDeviceItem(devIdx, "endPoints")
    eui = database.GetDeviceItem(devIdx, "eui64")
    if None != ep and None != eui: 
        pendingBinding = cluster
        return ("AT+BIND:"+devId+",3,"+eui+","+ep+","+cluster+","+database.GetDeviceItem(0, "eui64")+","+ourEp, "Bind")

def Prod(devIdx):    # Ask device a question, just to provoke a response                        
    devId = database.GetDeviceItem(devIdx, "nwkId")
    ep = database.GetDeviceItem(devIdx, "endPoints")
    if devId != None and ep != None:
        cmdRsp = telegesis.ReadAttr(devId, ep, zcl.Cluster.Basic, zcl.Attribute.Model_Name) # Get Basic's Device Name in order to prod it into life
        EnqueueCmd(devIdx, cmdRsp)

def Identify(devIdx, durationS):    # Duration in seconds to flash the device's LED.  Use duration=0 to stop.
    devId = database.GetDeviceItem(devIdx, "nwkId")
    ep = database.GetDeviceItem(devIdx, "endPoints")
    if devId and ep:
        durationStr = format(int(durationS), 'X').zfill(4)
        EnqueueCmd(devIdx, ["AT+IDENTIFY:"+devId+","+ep+",0,"+durationStr, "DFTREP"]) # Identify for selected time

def SwitchOn(devIdx):
    devId = database.GetDeviceItem(devIdx, "nwkId")
    ep = database.GetDeviceItem(devIdx, "endPoints")
    if devId and ep:
        SetTempVal(devIdx, "JustSentOnOff", "True")
        EnqueueCmd(devIdx, ["AT+RONOFF:"+devId+","+ep+",0,1", "OK"]) # Assume FFD if it supports OnOff cluster

def SwitchOff(devIdx):
    devId = database.GetDeviceItem(devIdx, "nwkId")
    ep = database.GetDeviceItem(devIdx, "endPoints")
    if devId and ep:
        DelTempVal(devIdx,"SwitchOff@") # Remove any pending "Off" events if we're turning the device off directly
        EnqueueCmd(devIdx, ["AT+LCMVTOLEV:"+devId+","+ep+",0,0,FE,0001", "OK"]) # Ensure fully bright ready to be turned on later
        SetTempVal(devIdx, "JustSentOnOff", "True")
        EnqueueCmd(devIdx, ["AT+RONOFF:"+devId+","+ep+",0,0", "OK"]) # Assume FFD if it supports OnOff cluster

def Toggle(devIdx):
    devId = database.GetDeviceItem(devIdx, "nwkId")
    ep = database.GetDeviceItem(devIdx, "endPoints")
    if devId and ep:
        DelTempVal(devIdx,"SwitchOff@") # Remove any pending "Off" events if we're handling the device directly
        SetTempVal(devIdx, "JustSentOnOff", "True")
        EnqueueCmd(devIdx, ["AT+RONOFF:"+devId+","+ep+",0", "OK"]) # Assume FFD if it supports OnOff cluster

def Dim(devIdx, level):
    devId = database.GetDeviceItem(devIdx, "nwkId")
    ep = database.GetDeviceItem(devIdx, "endPoints")
    if devId and ep:
        if level > 1:  # Assume it's a percentage
            level = level / 100 # Convert to a fraction
        levelStr = format(int(level * 254), 'X').zfill(2)
        EnqueueCmd(devIdx, ["AT+LCMVTOLEV:"+devId+","+ep+",0,1,"+levelStr+",000A", "DFTREP"]) # Fade over 1 sec (in 10ths)

def Hue(devIdx, hueDegree):
    devId = database.GetDeviceItem(devIdx, "nwkId")
    ep = database.GetDeviceItem(devIdx, "endPoints")
    if devId and ep:
        hueStr = format(int(float(hueDegree/360) * 254), 'X').zfill(2)
        EnqueueCmd(devIdx, ["AT+CCMVTOHUE:"+devId+","+ep+",0,"+hueStr+",00,0001", "DFTREP"]) # Fade over 100ms (in sec/10)

def Sat(devIdx, satPercentage):
    devId = database.GetDeviceItem(devIdx, "nwkId")
    ep = database.GetDeviceItem(devIdx, "endPoints")
    if devId and ep:
        satStr = format(int(float(satPercentage/100) * 254), 'X').zfill(2)
        EnqueueCmd(devIdx, ["AT+CCMVTOSAT:"+devId+","+ep+",0,"+satStr+",0001", "DFTREP"]) # Fade over 100ms (in sec/10)

def InitQueue(devIdx):
    global txQueue, expRsp, expRspTimeoutS
    txQueue.append([])
    expRsp.append("")
    expRspTimeoutS.append(0)

def EnqueueCmd(devIdx, cmdRsp):
    global txQueue
    if cmdRsp:
        log.debug("Queuing "+cmdRsp[0]+"  for devIdx "+str(devIdx))
        txQueue[devIdx].insert(0, cmdRsp)     # Insert [cmd,rsp] at the head of device's txQueue

def JumpQueueCmd(devIdx, cmdRsp):
    global txQueue
    if cmdRsp:
        log.debug("Jump-queuing "+cmdRsp[0]+"  for devIdx "+str(devIdx))
        txQueue[devIdx].append(cmdRsp)     # Append [cmd,rsp] at the head (thus force to the front) of device's txQueue

def DequeueCmd(devIdx):
    global txQueue
    if IsQueueEmpty(devIdx):
        return None
    else:
        log.debug("Un-queuing item for devIdx "+str(devIdx))
        return txQueue[devIdx].pop()    # Get last element

def IsQueueEmpty(devIdx):
    return txQueue[devIdx] == []

