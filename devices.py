#devices.py

from datetime import datetime
from datetime import timedelta
import time
from array import *
# App-specific modules
import events
import log
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
import synopsis
import heating

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
        if len(eventArg) >= 3:
            eui64 = eventArg[1]
            nwkId = eventArg[2]
            devKey = GetKey(nwkId)
            if devKey == None:  # Which will only be the case if we've not seen this short Id before
                devKey = database.GetDevKey("eui64", eui64)
                if devKey == None:  # Which will be the case if we've not seen the long Id either
                    devKey = Add(nwkId, eui64, eventArg[0])
                    log.debug("New key for new device is "+ str(devKey))
                    if eventArg[0] == "SED":
                        SetTempVal(devKey,"PollingUntil", datetime.now()+timedelta(seconds=300))
                    events.Issue(events.ids.NEWDEVICE, devKey)  # Tell everyone that a new device has been seen, so it can be initialised
                else:   # Same long Id, but short Id needs updating after it has changed
                    database.SetDeviceItem(devKey, "nwkId", nwkId)
            else:
                NoteMsgDetails(devKey, eventArg)
            SetTempVal(devKey, "GetNextBatteryAfter", datetime.now())    # Ask for battery shortly after Device Announce, either new or old one re-joining
    if eventId == events.ids.CHECKIN:   # See if we have anything to ask the device...
        if len(eventArg) >= 3:
            endPoint = eventArg[2]
            seq = "00" # was seq = eventArg[3], but that's the RSSI
            devKey = GetKey(eventArg[1])
            if devKey != None:
                EnsureInBinding(devKey, zcl.Cluster.PollCtrl)   # Assume CheckIn means PollCtrl must be in binding, so make sure this is up-to-date
                NoteMsgDetails(devKey, eventArg)
                if database.GetDeviceItem(devKey, "endPoints") == None:
                    database.SetDeviceItem(devKey, "endPoints", endPoint) # Note endpoint that CheckIn came from, unless we already know this
                nwkId = database.GetDeviceItem(devKey, "nwkId")
                cmdRsp = Check(devKey)   # Check to see if we want to know anything about the device
                if cmdRsp != None:
                    log.debug("Keep awake for 10 secs so we can send "+cmdRsp[0])
                    queue.Jump(devKey, ["AT+RAWZCL:"+nwkId+","+endPoint+",0020,11"+seq+"00012800", "DFTREP"]) # Tell device to enter Fast Poll for 40qs (==10s)
                    SetTempVal(devKey,"PollingUntil", datetime.now()+timedelta(seconds=10))
                    queue.EnqueueCmd(devKey, cmdRsp)  # This will go out after the Fast Poll Set
                else:
                    SetTempVal(devKey,"PollingUntil", datetime.now()+timedelta(seconds=2))  # Say that it's polling for a short while, so that we can tell it to stop(!)
                    queue.EnqueueCmd(devKey, ["AT+RAWZCL:"+nwkId+","+endPoint+",0020,11"+seq+"00000100", "DFTREP"]) # Tell device to stop Poll
            else: # Unknown device, so assume it's been deleted from our database
                telegesis.Leave(eventArg[1])    # Tell device to leave the network, since we don't know anything about it
    if eventId == events.ids.TRIGGER or eventId == events.ids.BUTTON:
        if len(eventArg) >= 2:
            devKey = GetKey(eventArg[1]) # Lookup device from network address in eventArg[1]
            if devKey != None:
                SetTempVal(devKey,"PollingUntil", datetime.now()+timedelta(seconds=1))  # Say that it's polling for a very short while so that we can try to set up a PollCtrl cluster
    if eventId == events.ids.RXMSG:
        if eventArg[0] == "AddrResp" and eventArg[1] == "00" and len(eventArg) >= 3:
            devKey = GetKey(eventArg[2])
            if devKey != None:
                database.SetDeviceItem(devKey,"eui64",eventArg[1])
        elif eventArg[0] == "ActEpDesc" and len(eventArg) >= 3:
            if "00" == eventArg[2]:
                devKey = GetKey(eventArg[1])
                if devKey != None:
                    database.SetDeviceItem(devKey, "endPoints", eventArg[3]) # Note first endpoint
        elif eventArg[0] == "SimpleDesc" and len(eventArg) >= 3:
            if "00" == eventArg[2]:
                globalDevKey = GetKey(eventArg[1]) # Is multi-line response, so expect rest of response and use this global index until it's all finished
            elif "82" == eventArg[2]:   # 82 == Invalid endpoint
                devKey = GetKey(eventArg[1])
                events.Issue(events.ids.RXERROR, int(eventArg[2],16)) # Tell system that we're aborting this command
        elif eventArg[0] == "InCluster" and len(eventArg) >= 2:
            if globalDevKey != None:
                database.SetDeviceItem(globalDevKey, "inClusters", str(eventArg[1:])) # Store whole list from arg[1] to arg[n]
        elif eventArg[0] == "OutCluster" and len(eventArg) >= 2:
            if globalDevKey != None:
                NoteMsgDetails(globalDevKey, eventArg)  # Must do this so that we can remove RSSI and LQI if they're there, to avoid these values being interpreted as clusters
                database.SetDeviceItem(globalDevKey, "outClusters", str(eventArg[1:])) # Store whole list from arg[1] to arg[n]
            globalDevKey = None # We've finished with this global for now
        elif eventArg[0] == "RESPATTR" and len(eventArg) >= 7:
            devKey = GetKey(eventArg[1])
            if devKey != None:
                NoteMsgDetails(devKey, eventArg)
                if len(eventArg) >= 7:  # Check for number of args after possibly removing RSSI and LQI
                    ep = eventArg[2]
                    clusterId = eventArg[3]
                    attrId = eventArg[4]
                    if "00" == eventArg[5]:
                        attrVal = eventArg[6]
                        SetAttrVal(devKey, clusterId, attrId, attrVal)
                    else:
                        SetAttrVal(devKey, clusterId, attrId, "Failed (error "+eventArg[5]+")") # So that we don't keep asking
        elif eventArg[0] == "RESPMATTR" and len(eventArg) >= 8:
            devKey = GetKey(eventArg[1])
            if devKey != None:
                NoteMsgDetails(devKey, eventArg)
                if len(eventArg) >= 8:  # Check for number of args after possibly removing RSSI and LQI
                    ep = eventArg[2]
                    mfgId = eventArg[3]
                    clusterId = eventArg[4]
                    attrId = eventArg[5]
                    if "00" == eventArg[6]:
                        attrVal = eventArg[7]
                        SetAttrVal(devKey, clusterId, attrId, attrVal)
        elif eventArg[0] == "REPORTATTR" and len(eventArg) >= 7:
            devKey = GetKey(eventArg[1])
            if devKey != None:
                ep = eventArg[2]
                clusterId = eventArg[3]
                attrId = eventArg[4]
                attrType = eventArg[5]
                attrVal = eventArg[6]
                NoteMsgDetails(devKey, eventArg)
                EnsureReporting(devKey, clusterId, attrId, attrVal) # Make sure reports are happening at the correct frequency and update device if not
                SetAttrVal(devKey, clusterId, attrId, attrVal)
                NoteReporting(devKey, clusterId, attrId)
            else: # Unknown device, so assume it's been deleted from our database
                telegesis.Leave(eventArg[1])    # Tell device to leave the network, since we don't know anything about it
        elif eventArg[0] == "Bind" and len(eventArg) >= 2:    # Binding Response from device
            devKey = GetKey(eventArg[1])
            if devKey != None:
                if pendingBinding != None:
                    binding = eval(database.GetDeviceItem(devKey, "binding", "[]"))
                    if pendingBinding not in binding:   # Only put it in once, even if we get multiple responses
                        binding.append(pendingBinding)
                        database.SetDeviceItem(devKey, "binding", str(binding))
                    pendingBinding = None
        elif eventArg[0] == "CFGRPTRSP" and len(eventArg) >= 5:   # Configure Report Response from device
            devKey = GetKey(eventArg[1])
            status = eventArg[4]
            if devKey != None and status == "00":
                clusterId = eventArg[3]
                attrId = pendingRptAttrId # Need to remember this, since it doesn't appear in CFGRPTRSP
                NoteReporting(devKey, clusterId, attrId)
                pendingRptAttrId = None # Ready for the next report
        elif eventArg[0] == "CWSCHEDULE":
            heating.ParseCWShedule(eventArg)
        #else:   # Unrecognised message, but we still want to extract OOB info
        #    if len(eventArg) >= 2:
        #        devKey = GetKey(eventArg[1])    # Assume this is sensible
        #        if devKey != None:
        #            NoteMsgDetails(devKey, eventArg)
    #if eventId == events.ids.BUTTON:
    #    devKey = GetKey(eventArg[1]) # Lookup device from network address in eventArg[1]
    #    NoteMsgDetails(devKey, eventArg)
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
                    DelTempVal(devKey, "SwitchOff@")
                    devcmds.SwitchOff(devKey)
            fadeDownAt = GetTempVal(devKey, "FadeDown@")
            if fadeDownAt:
                if datetime.now() >= fadeDownAt:
                    DelTempVal(devKey, "FadeDown@")
                    devcmds.Dim(devKey, 0)
            pirOffAt = GetTempVal(devKey, "PirInactive@")
            if pirOffAt:
                if datetime.now() >= pirOffAt:
                    DelTempVal(devKey, "PirInactive@")
                    newState = "inactive"
                    database.NewEvent(devKey, newState)
                    Rule(devKey, newState)
    #if eventId == events.ids.HOURS and eventArg == 4: # 4am, time to send timestamp to all devices with time cluster
    #    for devKey in devDict:  # Go through devDict, pulling out each entry
    #        if devDict[devKey] >= 0:    # Make sure device hasn't been deleted
    #            inClstr = database.GetDeviceItem(devKey, "inClusters") # Assume we have a list of clusters if we get this far
    #            if (zcl.Clusters.Time in inClstr): # Or should this be in the outClusters?
    #                iottime.SetTime(devKey, time.localtime()) # ToDo: Enable this when we're confident it'll work!
    # End event handler

def EnsureReporting(devKey, clstrId, attrId, attrVal): # Check when this attr last reported and update device's reporting if necessary
    if isnumeric(attrVal, 16):
        newVal = int(attrVal, 16) # Assume value arrives in hex
    else:
        return
    if clstrId == zcl.Cluster.SimpleMetering and attrId == zcl.Attribute.InstantaneousDemand:
        prevItem = database.GetLatestLoggedItem(devKey, "PowerReadingW")  # Check when we got last reading
        field = "powerReporting"
    elif clstrId == zcl.Cluster.SimpleMetering and attrId == zcl.Attribute.CurrentSummationDelivered:
        prevItem = database.GetLatestLoggedItem(devKey, "EnergyConsumedWh")
        field = "energyConsumedReporting"
    elif clstrId == zcl.Cluster.SimpleMetering and attrId == zcl.Attribute.CurrentSummationReceived:
        prevItem = database.GetLatestLoggedItem(devKey, "EnergyGeneratedWh")
        field = "energyGeneratedReporting"
    else: # Don't know how often it should report.  Could add temperature and battery
        return
    if prevItem != None:
        prevTime = prevItem[1]
        prevVal = prevItem[0]
        minMaxDelta = database.GetDeviceItem(devKey, field) # Look up min and max for this item
        if minMaxDelta != None:
            confList = minMaxDelta.split(",")
            min = int(confList[0])
            max = int(confList[1])
            delta = int(confList[2])
            change = abs(newVal - int(prevVal))
            secsSinceLastReport = (datetime.now() - datetime.strptime(prevTime, "%Y-%m-%d %H:%M:%S")).seconds  # Work out time between now and prevTime in seconds
            log.debug("Prev report "+str(secsSinceLastReport)+" s ago, min="+str(min)+" for devKey "+str(devKey)+" with old val="+str(prevVal)+" vs new val of "+str(newVal))
            if max == -1 or secsSinceLastReport < min or secsSinceLastReport > max: # Check whether min>secsSincelastReport>max or max==-1
                Config(devKey, field) # Re-configure device
            elif secsSinceLastReport < max-(max/10) and change<delta: # Check delta if not too close to max
                Config(devKey, field) # Re-configure device

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
    log.debug("New reporting entry of "+reporting+" with cluster:"+clusterId+" and attrId:"+attrId+" for devKey:"+str(devKey))
    EnsureInBinding(devKey, clusterId)   # Assume reportable items must be in binding for us to receive them, so make sure this is up-to-date

def EnsureInBinding(devKey, clusterId):  # Put clusterId in binding if not there already
    entry = database.GetDeviceItem(devKey, "binding", "[]")
    binding = eval(entry)
    #log.debug("Binding is "+str(binding))
    if clusterId not in binding:
        binding.append(clusterId)
        database.SetDeviceItem(devKey, "binding", str(binding))

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
            try:
                varVal = int(int(value, 16) / 2) # Arrives in 0.5% increments, but drop fractional component
            except ValueError:
                varVal = None
            if varVal != None:
                log.debug("Battery is "+str(varVal)+"%.  Get next reading at "+str(GetTempVal(devKey, "GetNextBatteryAfter")))
                database.LogItem(devKey, "BatteryPercentage", varVal) # For web page
                lowBatt = int(config.Get("lowBattery", "5"))
                if varVal < lowBatt:
                    devName = database.GetDeviceItem(devKey, "userName")
                    synopsis.problem(devName + "_batt", devName + " low battery ("+str(varVal)+"%)")
    if clstrId == zcl.Cluster.Temperature and attrId == zcl.Attribute.Celsius:
        if value != "FF9C" and value != "8000": # Don't know where this value (of -100) comes from, but seems to mean "Illegal temp", although it should be -1'C
            try:
                varVal = int(value, 16) / 100 # Arrives in 0.01'C increments 
                database.LogItem(devKey, "TemperatureCelsius", varVal) # For web page
            except ValueError:
                log.debug("Bad temperature of "+ value)
    if clstrId == zcl.Cluster.OnOff and attrId == zcl.Attribute.OnOffState:
        if isnumeric(value, 16):
            oldState = database.GetLatestLoggedValue(devKey, "State")
            if int(value, 16) == 0:
                newState = "SwitchOff"
            else:
                newState = "SwitchOn"
            if oldState != newState:
                database.UpdateLoggedItem(devKey, "State", newState) # So that we can access it from the rules later
                database.NewEvent(devKey, newState)
                Rule(devKey, newState)
            expectedState = GetTempVal(devKey, "ExpectOnOff")
            if expectedState != None:
                if newState != expectedState:
                    if expectedState == "SwitchOn":
                        devcmds.SwitchOn(devKey)  # Re-issue command
                    else: # Assume SwitchOff
                        devcmds.SwitchOff(devKey)  # Re-issue command
                else: # We got the expected result
                    DelTempVal(devKey, "ExpectOnOff")
    if clstrId == zcl.Cluster.Time and attrId == zcl.Attribute.LocalTime:
        if isnumeric(value, 16):
            varVal = int(value, 16) # Arrives in Watts, so store it in the same way
            log.debug("Raw time:"+str(varVal))
            timeStr = iottime.FromZigbee(varVal)
            log.debug("Human time:"+timeStr)
            database.UpdateLoggedItem(devKey, "Time", timeStr)  # Just store latest time string
    if clstrId == zcl.Cluster.SimpleMetering and attrId == zcl.Attribute.InstantaneousDemand:
        if isnumeric(value, 16):
            varVal = int(value, 16) # Arrives in Watts, so store it in the same way
            inClstr = database.GetDeviceItem(devKey, "inClusters") # Assume we have a list of clusters if we get this far
            if zcl.Cluster.OnOff not in inClstr:    # Device is powerclamp (has simplemetering but no OnOff)
                database.UpdateLoggedItem(devKey, "State", str(varVal)+"W") # So that we can access it from the rules later, or show it on the web
            database.UpdateLoggedItem(devKey, "PowerReadingW", varVal)  # Just store latest reading
    if clstrId == zcl.Cluster.SimpleMetering and attrId == zcl.Attribute.CurrentSummationDelivered:
        if isnumeric(value, 16):
            varVal = int(value, 16) # Arrives in accumulated WattHours, so store it in the same way
            database.LogItem(devKey, "EnergyConsumedWh", varVal)
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
    if clstrId == zcl.Cluster.PollCtrl:
        if attrId == zcl.Attribute.LongPollIntervalQs:
            varVal = str(float(int(value, 16) / 4))    # Value arrives in units of quarter seconds
            database.SetDeviceItem(devKey, "longPollInterval", varVal) # For web page and also to see whether to wait for CheckIn or just send messages (if <6 secs)
    if clstrId == zcl.Cluster.Thermostat:
        if attrId == zcl.Attribute.LocalTemp:
            if isnumeric(value, 16):
                varVal = int(value, 16) / 100 # Arrives in 0.01'C increments 
                database.LogItem(devKey, "SourceCelsius", varVal) # For web page
        if attrId == zcl.Attribute.OccupiedHeatingSetPoint:
            if isnumeric(value, 16):
                varVal = int(value, 16) / 100 # Arrives in 0.01'C increments 
                database.LogItem(devKey, "TargetCelsius", varVal) # For web page
    if clstrId == zcl.Cluster.Time:
        if attrId == zcl.Attribute.Time:
            if isnumeric(value, 16):
                varVal = int(value, 16) # Arrives in seconds since 1st Jan 2000
                timeStamp = iottime.FromZigbee(varVal)
                database.LogItem(devKey, "time", str(timeStamp)) # For web page

def Rule(devKey, state):
    userName = database.GetDeviceItem(devKey, "userName")
    if None != userName:
        rules.Run(userName+"=="+state)

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
            try:
                signal = int((int(lqi, 16) * 100) / 255)    # Convert 0-255 to 0-100.  Ignore RSSI for now
            except ValueError:
                signal = -1   # Cannot get signal
            if signal != -1:
                entry = database.GetLatestLoggedItem(devKey, "SignalPercentage")
                if entry != None:
                    oldSignal = entry[0] # Just the value
                    fmt = "%Y-%m-%d %H:%M:%S"
                    oldTimestamp = datetime.strptime(entry[1], fmt)
                    if oldSignal == None:
                        oldSignal = signal + 100  # Force an update if no previous signal
                    deltaSignal = signal - oldSignal
                    deltaTime = datetime.now() - oldTimestamp
                    if abs(deltaSignal) > 5:
                        if deltaTime.seconds > 600:  # Only note signal level that's different enough and at least 10 minutes since last one
                            database.LogItem(devKey, "SignalPercentage", signal)
                    else:   # signal is sufficiently similar to last one, so update timestamp
                        database.RefreshLoggedItem(devKey, "SignalPercentage")  # Update timestamp to avoid too many >10 minutes!
            arg.remove(rssi)
            arg.remove(lqi)

def isnumeric(item, base=10):
    try:
        val = int(item, base)
        return True
    except ValueError:
        return False

def Check(devKey):
    global pendingBinding, msp_ota
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
    binding = database.GetDeviceItem(devKey, "binding" "[]")
    if binding == None:
        log.debug("No binding for devKey "+str(devKey))
        return None
    if inClstr != None:
        if pendingBinding == None:  # Only try to add one binding at once
            if zcl.Cluster.PollCtrl in inClstr and zcl.Cluster.PollCtrl not in binding:
                return SetBinding(devKey, zcl.Cluster.PollCtrl, "01") # 01 is our endpoint we want messages to come to
            if zcl.Cluster.OnOff in outClstr and zcl.Cluster.OnOff not in binding: # If device sends OnOff commands...
                return SetBinding(devKey, zcl.Cluster.OnOff, "0A") # 0A is our endpoint we want messages to come to (so that we get TOGGLE, ON and OFF commands)
            if zcl.Cluster.Temperature in inClstr and zcl.Cluster.Temperature not in binding:
                return SetBinding(devKey, zcl.Cluster.Temperature, "01") # 01 is our endpoint we want messages to come to
            if zcl.Cluster.SimpleMetering in inClstr and zcl.Cluster.SimpleMetering not in binding:
                return SetBinding(devKey, zcl.Cluster.SimpleMetering, "01") # 01 is our endpoint we want messages to come to
            if zcl.Cluster.Thermostat in inClstr and zcl.Cluster.Thermostat not in binding:
                return SetBinding(devKey, zcl.Cluster.Thermostat, "01") # 01 is our endpoint we want messages to come to
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
                    log.debug("Now = "+str(datetime.now())+" and checkBatt = "+str(checkBatt))
                    return telegesis.ReadAttr(nwkId, ep, zcl.Cluster.PowerConfig, zcl.Attribute.Batt_Percentage) # Get Battery percentage
        if zcl.Cluster.PollCtrl in inClstr:
            if None == database.GetDeviceItem(devKey, "longPollInterval"):
                return telegesis.ReadAttr(nwkId, ep, zcl.Cluster.PollCtrl, zcl.Attribute.LongPollIntervalQs) # Get Poll Control's Long poll interval
        if zcl.Cluster.OTA in outClstr:
            if None == database.GetDeviceItem(devKey, "firmwareVersion"):
                return ("AT+READCATR:"+nwkId+","+ep+",0,"+zcl.Cluster.OTA+","+zcl.Attribute.firmwareVersion, "RESPATTR") # Get OTA's Version number as a string of hex digits
        if msp_ota != None and msp_ota in outClstr:
            if None == database.GetDeviceItem(devKey, "firmwareVersion"):
                return ("AT+READMCATR:"+nwkId+","+ep+",0,"+config.Get(mfgId)+","+msp_ota+","+zcl.Attribute.firmwareVersion, "RESPMATTR") # Get OTA's Version number as a string of hex digits
        reporting = database.GetDeviceItem(devKey, "reporting", "[]")
        if zcl.Cluster.PowerConfig in binding and "SED"== database.GetDeviceItem(devKey, "devType"):
            atCmd = CheckReporting(devKey, reporting, "batteryReporting", zcl.Cluster.PowerConfig, zcl.Attribute.Batt_Percentage, zcl.AttributeTypes.Uint8, "43200,43200,2")    # Default temperature reporting is "Every 12 hours"
            if atCmd != None:
                return atCmd
        if zcl.Cluster.Temperature in binding:
            atCmd = CheckReporting(devKey, reporting, "temperatureReporting", zcl.Cluster.Temperature, zcl.Attribute.Celsius, zcl.AttributeTypes.Uint16, "300,3600,100")    # Default temperature reporting is "between 5 mins and 1 hr, or +/- 1.00'C"
            if atCmd != None:
                return atCmd
        if zcl.Cluster.SimpleMetering in binding:
            atCmd = CheckReporting(devKey, reporting, "powerReporting", zcl.Cluster.SimpleMetering, zcl.Attribute.InstantaneousDemand, zcl.AttributeTypes.Sint24, "-1,-1,10")    # Default power reporting is "between 5 seconds and 15 minutes, or +/- 10W"
            if atCmd != None:
                return atCmd
            atCmd = CheckReporting(devKey, reporting, "energyConsumedReporting", zcl.Cluster.SimpleMetering, zcl.Attribute.CurrentSummationDelivered, zcl.AttributeTypes.Uint48, "-1,-1,100")    # Default energy consumed reporting is "between 1 minute and 15 minutes, or +100Wh"
            if atCmd != None:
                return atCmd
            atCmd = CheckReporting(devKey, reporting, "energyGeneratedReporting", zcl.Cluster.SimpleMetering, zcl.Attribute.CurrentSummationReceived, zcl.AttributeTypes.Uint48, "-1,-1,0")    # Default energy generated reporting is "never" (-1 as max)
            if atCmd != None:
                return atCmd
        if zcl.Cluster.Thermostat in binding:
            atCmd = CheckReporting(devKey, reporting, "targetTempReporting", zcl.Cluster.Thermostat, zcl.Attribute.OccupiedHeatingSetPoint, zcl.AttributeTypes.Sint16, "60,900,100")    # Default target temperature reporting is "between 1 minute and 15 minutes, or +/-1.00'C"
            if atCmd != None:
                return atCmd
    if GetTempVal(devKey, "JustSentOnOff"):
        DelTempVal(devKey, "JustSentOnOff")
        return telegesis.ReadAttr(nwkId, ep, zcl.Cluster.OnOff, zcl.Attribute.OnOffState) # Get OnOff state after sending toggle
    return None

def IsListening(devKey):
    type = database.GetDeviceItem(devKey, "devType")
    if type == "SED":
        pollFreq = database.GetDeviceItem(devKey, "longPollInterval")   # See if the device is a fast poller
        if pollFreq != None:
            if float(pollFreq) < 6.0:
                return True
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

def CheckReporting(devKey, reporting, field, cluster, attrId, attrType, defVal):
    global pendingRptAttrId
    rpt = cluster+":"+attrId
    if pendingRptAttrId == None and rpt not in reporting:
        pendingRptAttrId = attrId
        devRpt = database.GetDeviceItem(devKey, field, defVal)
        rptList = devRpt.split(",") # Explode the CSV line to a list of min, max, delta
        if "-1" == rptList[0]:
            return  # Don't configure this attribute for reporting if min==-1 
        log.debug("Update device reporting for "+database.GetDeviceItem(devKey, "userName")+"'s "+field)
        log.debug("Reporting was "+reporting+" which didn't include " + rpt)
        if attrType == zcl.AttributeTypes.Uint8 or attrType == zcl.AttributeTypes.Sint8:
            deltaLen = 2   # Need to know number of digits to use in deltaHex
        elif attrType == zcl.AttributeTypes.Uint16 or attrType == zcl.AttributeTypes.Sint16:
            deltaLen = 4   # Need to know number of digits to use in deltaHex
        elif attrType == zcl.AttributeTypes.Uint24 or attrType == zcl.AttributeTypes.Sint24:
            deltaLen = 6   # Need to know number of digits to use in deltaHex
        elif attrType == zcl.AttributeTypes.Uint32 or attrType == zcl.AttributeTypes.Sint32:
            deltaLen = 8   # Need to know number of digits to use in deltaHex
        elif attrType == zcl.AttributeTypes.Uint48:
            deltaLen = 12   # Need to know number of digits to use in deltaHex
        else:
            deltaLen = 0    # Don't know format, so fail
        if deltaLen != 0:
            deltaLenFmt = "%0."+str(deltaLen)+"X"   # Work out how many digits to use given the attribute type
            minHex = "%0.4X" % int(rptList[0]) # Convert each decimal item to a hex string
            if int(rptList[1]) == -1:
                maxHex = "FFFF" # To disable this report
            else:
                maxHex = "%0.4X" % int(rptList[1])
            deltaHex = deltaLenFmt % int(rptList[2])    # Use the correct number of leading zeros for delta's hex representation
            nwkId = database.GetDeviceItem(devKey, "nwkId")
            ep = database.GetDeviceItem(devKey, "endPoints")
            return ("AT+CFGRPT:"+nwkId+","+ep+",0,"+cluster+",0,"+attrId+","+attrType+","+minHex+","+maxHex+","+deltaHex, "CFGRPTRSP")
    return None

def Config(devKey, field):
    # Read newly changed field from database for device and use this to update actual device ASAP
    log.debug("Updating reporting for "+field)
    reporting = database.GetDeviceItem(devKey, "reporting") # See if we're expecting this report, and note it in the reporting table
    if field=="batteryReporting":
        rptToUpdate = zcl.Cluster.PowerConfig+":"+zcl.Attribute.Batt_Percentage
    elif field=="temperatureReporting":
        rptToUpdate = zcl.Cluster.Temperature+":"+zcl.Attribute.Celsius
    elif field=="powerReporting":
        rptToUpdate = zcl.Cluster.SimpleMetering+":"+zcl.Attribute.InstantaneousDemand
    elif field=="energyConsumedReporting":
        rptToUpdate = zcl.Cluster.SimpleMetering+":"+zcl.Attribute.CurrentSummationDelivered
    elif field=="energyGeneratedReporting":
        rptToUpdate = zcl.Cluster.SimpleMetering+":"+zcl.Attribute.CurrentSummationReceived
    else:
        rptToUpdate = None
    if reporting != None and rptToUpdate != None:
        reportList = eval(reporting)
        if rptToUpdate in reportList:
            reportList.remove(rptToUpdate)   # Remove newly changed item from list so that Check() routine will spot this and update the reporting accordingly
            updatedReporting = str(reportList)
            database.SetDeviceItem(devKey, "reporting", updatedReporting) # Ready for Check() to send new item

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

