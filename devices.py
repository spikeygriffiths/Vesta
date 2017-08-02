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
import config
import devcmds
import queue
import status

globalDevKey = None
pendingBinding = None # Needed because the BIND response doesn't include the cluster
pendingRptAttrId = None # Needed because CFGRPTRSP only includes the cluster and not the attr

# Keep a track of known devices present in the system
devDict = {}    # A dictionary of devKey : index, to allow devices to be added and removed from the database without disturbing their queues, ephemera, etc.
ephemera = [] # Don't bother saving this
expRsp = [] # List of expected responses for each device
expRspTimeoutS = array('f',[]) # Array of timeouts if we're expecting a response, one per device
msp_ota = None  # Until filled in from config

def EventHandler(eventId, eventArg):
    global ephemera, globalDevKey, pendingBinding, pendingRptAttrId, msp_ota
    if eventId == events.ids.PREINIT:
        keyList = database.GetAllDevKeys()  # Get a list of all the device identifiers from the database
        for devKey in keyList:  # Hub and devices
            Init(devKey) # Initialise dictionary and associated ephemera
            if database.GetDeviceItem(devKey, "nwkId") != "0000":  # Ignore hub
                SetTempVal(devKey, "GetNextBatteryAfter", datetime.now())    # Ask for battery shortly after startup
    if eventId == events.ids.INIT:
        msp_ota = config.Get("MSP_OTA")
    if eventId == events.ids.DEVICE_ANNOUNCE:
        nwkId = eventArg[2]
        devKey = GetKey(nwkId)
        if devKey == None:  # Which will only be the case if this device is actually new, and not just reset and announced
            devKey = Add(nwkId, eventArg[1], eventArg[0])
            log.debug("New key for new device is "+ str(devKey))
            if eventArg[0] == "SED":
                SetTempVal(devKey,"PollingUntil", datetime.now()+timedelta(seconds=300))
            events.Issue(events.ids.NEWDEVICE, devKey)  # Tell everyone that a new device has been seen, so it can be initialised
        else:
            NoteMsgDetails(devKey, eventArg)
    if eventId == events.ids.CHECKIN:   # See if we have anything to ask the device...
        endPoint = eventArg[2]
        seq = "00" # was seq = eventArg[3], but that's the RSSI
        devKey = GetKey(eventArg[1])
        if devKey != None:
            NoteMsgDetails(devKey, eventArg)
            if database.GetDeviceItem(devKey, "endPoints") == None:
                database.SetDeviceItem(devKey, "endPoints", endPoint) # Note endpoint that CheckIn came from, unless we already know this
            nwkId = database.GetDeviceItem(devKey, "nwkId")
            cmdRsp = Check(devKey)   # Check to see if we want to know anything about the device
            if cmdRsp != None:
                log.debug("Keep awake for 10 secs")
                queue.Jump(devKey, ["AT+RAWZCL:"+nwkId+","+endPoint+",0020,11"+seq+"00012800", "DFTREP"]) # Tell device to enter Fast Poll for 40qs (==10s)
                SetTempVal(devKey,"PollingUntil", datetime.now()+timedelta(seconds=10))
                queue.EnqueueCmd(devKey, cmdRsp)  # This will go out after the Fast Poll Set
            else:
                SetTempVal(devKey,"PollingUntil", datetime.now()+timedelta(seconds=2))  # Say that it's polling for a short while, so that we can tell it to stop(!)
                queue.EnqueueCmd(devKey, ["AT+RAWZCL:"+nwkId+","+endPoint+",0020,11"+seq+"00000100", "DFTREP"]) # Tell device to stop Poll
        else: # Unknown device, so assume it's been deleted from our database
            telegesis.Leave(eventArg[1])    # Tell device to leave the network, since we don't know anything about it
    if eventId == events.ids.RXMSG:
        if eventArg[0] == "AddrResp" and eventArg[1] == "00":
            devKey = GetKey(eventArg[2])
            if devKey != None:
                database.SetDeviceItem(devKey,"eui64",eventArg[1])
        elif eventArg[0] == "ActEpDesc":
            if "00" == eventArg[2]:
                devKey = GetKey(eventArg[1])
                if devKey != None:
                    database.SetDeviceItem(devKey, "endPoints", eventArg[3]) # Note first endpoint
        elif eventArg[0] == "SimpleDesc":
            if "00" == eventArg[2]:
                globalDevKey = GetKey(eventArg[1]) # Is multi-line response, so expect rest of response and use this global index until it's all finished
            elif "82" == eventArg[2]:   # 82 == Invalid endpoint
                devKey = GetKey(eventArg[1])
                events.Issue(events.ids.RXERROR, int(eventArg[2],16)) # Tell system that we're aborting this command
        elif eventArg[0] == "InCluster":
            if globalDevKey != None:
                database.SetDeviceItem(globalDevKey, "inClusters", str(eventArg[1:])) # Store whole list from arg[1] to arg[n]
        elif eventArg[0] == "OutCluster":
            if globalDevKey != None:
                NoteMsgDetails(globalDevKey, eventArg)
                database.SetDeviceItem(globalDevKey, "outClusters", str(eventArg[1:])) # Store whole list from arg[1] to arg[n]
            globalDevKey = None # We've finished with this global for now
        elif eventArg[0] == "RESPATTR":
            devKey = GetKey(eventArg[1])
            if devKey != None:
                NoteMsgDetails(devKey, eventArg)
                ep = eventArg[2]
                clusterId = eventArg[3]
                attrId = eventArg[4]
                if "00" == eventArg[5]:
                    attrVal = eventArg[6]
                    SetAttrVal(devKey, clusterId, attrId, attrVal)
                else:
                    SetAttrVal(devKey, clusterId, attrId, "Failed (error "+eventArg[5]+")") # So that we don't keep asking
        elif eventArg[0] == "RESPMATTR":
            devKey = GetKey(eventArg[1])
            if devKey != None:
                NoteMsgDetails(devKey, eventArg)
                ep = eventArg[2]
                mfgId = eventArg[3]
                clusterId = eventArg[4]
                attrId = eventArg[5]
                if "00" == eventArg[6]:
                    attrVal = eventArg[7]
                    SetAttrVal(devKey, clusterId, attrId, attrVal)
        elif eventArg[0] == "REPORTATTR":
            devKey = GetKey(eventArg[1])
            if devKey != None:
                ep = eventArg[2]
                clusterId = eventArg[3]
                attrId = eventArg[4]
                attrType = eventArg[5]
                attrVal = eventArg[6]
                NoteMsgDetails(devKey, eventArg)
                SetAttrVal(devKey, clusterId, attrId, attrVal)
                NoteReporting(devKey, clusterId, attrId)
            else: # Unknown device, so assume it's been deleted from our database
                telegesis.Leave(eventArg[1])    # Tell device to leave the network, since we don't know anything about it
        elif eventArg[0] == "Bind":    # Binding Response from device
            devKey = GetKey(eventArg[1])
            if devKey != None:
                if pendingBinding != None:
                    binding = eval(database.GetDeviceItem(devKey, "binding"))
                    if pendingBinding not in binding:   # Only put it in once, even if we get multiple responses
                        binding.append(pendingBinding)
                        database.SetDeviceItem(devKey, "binding", str(binding))
                    pendingBinding = None
        elif eventArg[0] == "CFGRPTRSP":   # Configure Report Response from device
            devKey = GetKey(eventArg[1])
            status = eventArg[4]
            if devKey != None and status == "00":
                clusterId = eventArg[3]
                attrId = pendingRptAttrId # Need to remember this, since it doesn't appear in CFGRPTRSP
                NoteReporting(devKey, clusterId, attrId)
        else:   # Unrecognised message, but we still want to extract OOB info
            if len(eventArg) >= 2:
                devKey = GetKey(eventArg[1])    # Assume this is sensible
                if devKey != None:
                    NoteMsgDetails(devKey, eventArg)
    if eventId == events.ids.BUTTON:
        devKey = GetKey(eventArg[1]) # Lookup device from network address in eventArg[1]
        NoteMsgDetails(devKey, eventArg)
    if eventId == events.ids.RXERROR:
        globalDevKey = None # We've finished with this global if we get an error
    if eventId == events.ids.SECONDS:
        for devKey in devDict:  # Go through devDict, pulling out each entry
            if devDict[devKey] >= 0:    # Make sure device hasn't been deleted
                if IsListening(devKey):  # True if FFD, ZED or Polling
                    devIndex = GetIndexFromKey(devKey)
                    if expRsp[devIndex] == None:  # We don't have a message in flight
                        if queue.IsEmpty(devKey):
                            cmdRsp = Check(devKey)
                            if cmdRsp:
                                queue.EnqueueCmd(devKey, cmdRsp)   # Queue up anything we ought to know
                        cmdRsp = queue.DequeueCmd(devKey) # Pull first item from queue
                        if cmdRsp != None:
                            log.debug("Sending "+str(cmdRsp))
                            expRsp[devIndex] = cmdRsp[1]  # Note response
                            expRspTimeoutS[devIndex] = 2  # If we've not heard back after 2 seconds, it's probably got lost, so try again
                            telegesis.TxCmd(cmdRsp[0])  # Send command directly
                    else:   # We're expecting a response, so time it out
                        expRspTimeoutS[devIndex] = expRspTimeoutS[devIndex] - eventArg
                        if expRspTimeoutS[devIndex] <= 0:
                            expRsp[devIndex] = None
            offAt = GetTempVal(devKey, "SwitchOff@")
            if offAt:
                if datetime.now() >= offAt:
                    devcmds.SwitchOff(devKey)
            pirOffAt = GetTempVal(devKey, "PirInactive@")
            if pirOffAt:
                if datetime.now() >= pirOffAt:
                    DelTempVal(devKey, "PirInactive@")
                    newState = "inactive"
                    database.NewEvent(devKey, newState)
                    Rule(devKey, newState)
    # End event handler

def NoteReporting(devKey, clusterId, attrId):
    reporting = database.GetDeviceItem(devKey, "reporting") # See if we're expecting this report, and note it in the reporting table
    newRpt = clusterId+":"+attrId
    if reporting != None:
        reportList = eval(reporting)
        if newRpt not in reportList:
            reportList.append(newRpt)
            reporting = str(reportList)
    else:
        reporting = "['"+newRpt+"']"
    database.SetDeviceItem(devKey, "reporting", reporting) # Ready for next time

def GetKey(nwkId):
    return database.GetDevKey("nwkId", nwkId)

def FindDev(nwkId):
    devKey = database.GetDevKey("userName", nwkId) # Try name first
    if devKey:
        return devKey
    return GetKey(nwkId)   # Try nwkId if no name match

def SetAttrVal(devKey, clstrId, attrId, value):
    global msp_ota
    if clstrId == zcl.Cluster.PowerConfig and attrId == zcl.Attribute.Batt_Percentage:
        SetTempVal(devKey, "GetNextBatteryAfter", datetime.now()+timedelta(seconds=86400))    # Ask for battery every day
        if value != "FF":
            varVal = int(int(value, 16) / 2) # Arrives in 0.5% increments, but drop fractional component
            #log.debug("Battery is "+str(varVal)+"%.  Get next reading at "+str(GetTempVal(devKey, "GetNextBatteryAfter")))
            database.SetStatus(devKey, "battery", varVal) # For web page
            if varVal < 10: # Batteries below 10% are considered "low"
                devName = database.GetDeviceItem(devKey, "userName")
                status.problem(devName + "_batt", devName + " low battery ("+str(varVal)+"%)")
    if clstrId == zcl.Cluster.Temperature and attrId == zcl.Attribute.Celsius:
        if value != "FF9C": # Don't know where this value (of -100) comes from - should be "7FFF" (signed value)
            varVal = int(value, 16) / 100 # Arrives in 0.01'C increments 
            database.SetStatus(devKey, "temperature", varVal) # For web page
    if clstrId == zcl.Cluster.OnOff and attrId == zcl.Attribute.OnOffState:
        oldState = database.GetLatestEvent(devKey)
        if int(value, 16) == 0:
            newState = "SwitchedOff"
        else:
            newState = "SwitchedOn"
        if oldState != newState:
            database.NewEvent(devKey, newState)
            Rule(devKey, newState)
    if clstrId == zcl.Cluster.SimpleMetering and attrId == zcl.Attribute.InstantaneousDemand:
        varVal = int(value, 16) # Arrives in Watts, so store it in the same way
        database.SetStatus(devKey, "powerReadingW", varVal)
    if clstrId == zcl.Cluster.IAS_Zone and attrId == zcl.Attribute.Zone_Type:
        database.SetDeviceItem(devKey, "iasZoneType", value)
    if clstrId == zcl.Cluster.Basic:
        if attrId == zcl.Attribute.Model_Name:
            database.SetDeviceItem(devKey, "modelName", value)
        if attrId == zcl.Attribute.Manuf_Name:
            database.SetDeviceItem(devKey, "manufName", value)
    if clstrId == zcl.Cluster.OTA or clstrId == msp_ota:
        if attrId == zcl.Attribute.firmwareVersion:
            database.SetDeviceItem(devKey, "firmwareVersion", value)

def Rule(devKey, state):
    rules.Run(database.GetDeviceItem(devKey, "userName")+"=="+state)

def SetTempVal(devKey, name, value):
    global ephemera
    devIndex = GetIndexFromKey(devKey)
    for item in ephemera[devIndex]:
        if item[0] == name:
            ephemera[devIndex].remove(item) # Remove old tuple if necessary
    ephemera[devIndex].append((name, value)) # Add new one regardless
    
def GetTempVal(devKey, name):
    global ephemera
    devIndex = GetIndexFromKey(devKey)
    for item in ephemera[devIndex]:
        if item[0] == name:
            return item[1] # Just return value associated with name
    return None # Indicate item not found

def DelTempVal(devKey, name):
    global ephemera
    devIndex = GetIndexFromKey(devKey)
    for item in ephemera[devIndex]:
        if item[0] == name:
            oldValue = item[1]
            ephemera[devIndex].remove(item) # Remove old tuple if necessary
            return oldValue # Just return old value associated with name before it was deleted
    return None # Indicate item not found

def NoteMsgDetails(devKey, arg):
    devIndex = GetIndexFromKey(devKey)
    if arg[0] == expRsp[devIndex]:
        expRsp[devIndex] = None   # Note that we've found the expected response now, so we're now clear to send
    presence.Set(devKey, presence.states.present) # Note presence
    if isnumeric(arg[-2]):
        if int(arg[-2]) < 0: # Assume penultimate item is RSSI, and thus that ultimate one is LQI
            rssi = arg[-2]
            lqi = arg[-1]
            signal = int((int(lqi, 16) * 100) / 255)    # Convert 0-255 to 0-100.  Ignore RSSI for now
            database.SetStatus(devKey, "signal", signal)
            arg.remove(rssi)
            arg.remove(lqi)

def isnumeric(item):
    try:
        val = int(item)
        return True
    except ValueError:
        return False

def Check(devKey):
    global pendingBinding, pendingRptAttrId, msp_ota
    if devKey == 0:
        return  # We don't need anything from the hub
    nwkId = database.GetDeviceItem(devKey, "nwkId")
    if nwkId == None:
        return  # Make sure it's a real device before continuing (it may have just been deleted)
    ep = database.GetDeviceItem(devKey, "endPoints")
    eui = database.GetDeviceItem(devKey, "eui64")
    inClstr = database.GetDeviceItem(devKey, "inClusters") # Assume we have a list of clusters if we get this far
    outClstr = database.GetDeviceItem(devKey, "outClusters")
    if None == ep:
        return ("AT+ACTEPDESC:"+nwkId+","+nwkId, "ActEpDesc")
    if None == eui:
        return ("AT+EUIREQ:"+nwkId+","+nwkId, "AddrResp")
    if None == inClstr or None == outClstr:
        database.SetDeviceItem(devKey, "outClusters", "[]") # Some devices have no outclusters...
        return ("AT+SIMPLEDESC:"+nwkId+","+nwkId+","+ep, "OutCluster")
    binding = database.GetDeviceItem(devKey, "binding")
    rprtg = database.GetDeviceItem(devKey, "reporting")
    if inClstr != None:
        if binding != None and pendingBinding == None:  # Only try to add one binding at once
            if zcl.Cluster.PollCtrl in inClstr and zcl.Cluster.PollCtrl not in binding:
                return SetBinding(devKey, zcl.Cluster.PollCtrl, "01") # 01 is our endpoint we want messages to come to
            if zcl.Cluster.OnOff in outClstr and zcl.Cluster.OnOff not in binding: # If device sends OnOff commands...
                return SetBinding(devKey, zcl.Cluster.OnOff, "0A") # 0A is our endpoint we want messages to come to (so that we get TOGGLE, ON and OFF commands)
            if zcl.Cluster.Temperature in inClstr and zcl.Cluster.Temperature not in binding:
                return SetBinding(devKey, zcl.Cluster.Temperature, "01") # 01 is our endpoint we want messages to come to
            if zcl.Cluster.SimpleMetering in inClstr and zcl.Cluster.SimpleMetering not in binding:
                return SetBinding(devKey, zcl.Cluster.SimpleMetering, "01") # 01 is our endpoint we want messages to come to
        else:
            database.SetDeviceItem(devKey, "binding", "[]")
        if zcl.Cluster.IAS_Zone in inClstr:
            if None == database.GetDeviceItem(devKey, "iasZoneType"):
                return telegesis.ReadAttr(nwkId, ep, zcl.Cluster.IAS_Zone, zcl.Attribute.Zone_Type) # Get IAS device type (PIR or contact, etc.)
        if zcl.Cluster.Basic in inClstr:
            if None == database.GetDeviceItem(devKey, "modelName"):
                return telegesis.ReadAttr(nwkId, ep, zcl.Cluster.Basic, zcl.Attribute.Model_Name) # Get Basic's Device Name
            if None == database.GetDeviceItem(devKey, "manufName"):
                return telegesis.ReadAttr(nwkId, ep, zcl.Cluster.Basic, zcl.Attribute.Manuf_Name) # Get Basic's Manufacturer Name
        if zcl.Cluster.PowerConfig in inClstr and "SED"== database.GetDeviceItem(devKey, "devType"):
            checkBatt = GetTempVal(devKey, "GetNextBatteryAfter")
            if checkBatt != None:
                if datetime.now() > checkBatt:
                    #log.debug("Now = "+str(datetime.now())+" and checkBatt = "+str(checkBatt))
                    return telegesis.ReadAttr(nwkId, ep, zcl.Cluster.PowerConfig, zcl.Attribute.Batt_Percentage) # Get Battery percentage
        if zcl.Cluster.OTA in outClstr:
            if None == database.GetDeviceItem(devKey, "firmwareVersion"):
                return ("AT+READCATR:"+nwkId+","+ep+",0,"+zcl.Cluster.OTA+","+zcl.Attribute.firmwareVersion, "RESPATTR") # Get OTA's Version number as a string of hex digits
        if msp_ota != None and msp_ota in outClstr:
            if None == database.GetDeviceItem(devKey, "firmwareVersion"):
                return ("AT+READMCATR:"+nwkId+","+ep+",0,"+config.Get(mfgId)+","+msp_ota+","+zcl.Attribute.firmwareVersion, "RESPMATTR") # Get OTA's Version number as a string of hex digits
        if rprtg != None:
            if zcl.Cluster.Temperature in inClstr:
                tmpRpt = zcl.Cluster.Temperature+":"+zcl.Attribute.Celsius
                if zcl.Cluster.Temperature in binding and tmpRpt not in rprtg:
                    pendingRptAttrId = zcl.Attribute.Celsius
                    return ("AT+CFGRPT:"+nwkId+","+ep+",0,"+zcl.Cluster.Temperature+",0,"+zcl.Attribute.Celsius+","+zcl.AttributeTypes.Uint16+",012C,0E10,0064", "CFGRPTRSP") # 012C is 300==5 mins, 0E10 is 3600==1 hour, 0064 is 100, being 1.00'C
            if zcl.Cluster.SimpleMetering in inClstr:
                tmpRpt = zcl.Cluster.SimpleMetering+":"+zcl.Attribute.InstantaneousDemand
                if zcl.Cluster.SimpleMetering in binding and tmpRpt not in rprtg:
                    pendingRptAttrId = zcl.Attribute.InstantaneousDemand
                    return ("AT+CFGRPT:"+nwkId+","+ep+",0,"+zcl.Cluster.SimpleMetering+",0,"+zcl.Attribute.InstantaneousDemand+","+zcl.AttributeTypes.Sint24+",0005,003C,00000A", "CFGRPTRSP") # 5 second minimum, 1 minute maximum, 10 watt change
        else:
            database.SetDeviceItem(devKey, "reporting", "[]")
    if GetTempVal(devKey, "JustSentOnOff"):
        DelTempVal(devKey, "JustSentOnOff")
        return telegesis.ReadAttr(nwkId, ep, zcl.Cluster.OnOff, zcl.Attribute.OnOffState) # Get OnOff state after sending toggle
    return None

def IsListening(devKey):
    type = database.GetDeviceItem(devKey, "devType")
    if type == "SED":
        pollTime = GetTempVal(devKey, "PollingUntil")
        if pollTime != None:
            if datetime.now() < pollTime:
                return True
        return False
    else: # Assume not sleepy
        return True # These devices are always awake and listening

def SetBinding(devKey, cluster, ourEp):
    global pendingBinding
    nwkId = database.GetDeviceItem(devKey, "nwkId")
    ep = database.GetDeviceItem(devKey, "endPoints")
    eui = database.GetDeviceItem(devKey, "eui64")
    if None != ep and None != eui: 
        pendingBinding = cluster
        return ("AT+BIND:"+nwkId+",3,"+eui+","+ep+","+cluster+","+database.GetDeviceItem(0, "eui64")+","+ourEp, "Bind")

def GetKeyFromIndex(idx):
    for key in devDict:
        if devDict[key] == idx:
            return key

def GetIndexFromKey(key):
    #log.debug("Looking up index for Key "+str(key))
    return devDict[key]

def Add(nwkId, eui64, devType):
    devKey = database.NewDevice(nwkId, eui64, devType)
    Init(devKey)
    return devKey

def Init(devKey):
    global expRsp, expRspTimeoutS
    index = len(ephemera)   # Rely upon the length of this as the master for making a new index into everything else!
    devDict[devKey] = index # Add new item
    #log.debug("Added new item to devDict, which now is "+str(devDict))
    ephemera.append([]) # Add parallel ephemeral device list
    queue.Init(devKey)
    expRsp.append("")
    expRspTimeoutS.append(0)
    return devKey

def Remove(devKey):
    if IsListening(devKey):
        nwkId = database.GetDeviceItem(devKey, "nwkId")
        if nwkId:
            telegesis.Leave(nwkId)    # Tell device to leave the network immediately (assuming it's listening)
    database.RemoveDevice(devKey)
    devDict[devKey] = -1    # Remove link between the key and its index (but don't remove the entry in the dict)
    # Note that the entry isn't removed, so that we deliberately leave the old queues and other ephemera so that we don't have to re-number all other items.
    # This should be OK, since they'll only amount to a few K (at most) for each device, and it shouldn't happen very often.
    # The lists will be re-built when the app restarts anyway.

