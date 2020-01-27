# devcmds.py

# App-specific modules
import devices
import devcmds
import queue
import database
import telegesis
import zcl
import log

def Prod(devKey):    # Ask device a question, just to provoke a response
    nwkId = database.GetDeviceItem(devKey, "nwkId")
    ep = database.GetDeviceItem(devKey, "endPoints")
    if nwkId != None and ep != None:
        log.debug("Prodding devKey "+str(devKey)+" (nwkId:"+nwkId+")")
        cmdRsp = telegesis.ReadAttr(nwkId, ep, zcl.Cluster.Basic, zcl.Attribute.Model_Name) # Get Basic's Device Name in order to prod it into life
        queue.EnqueueCmd(devKey, cmdRsp)

def Identify(devKey, durationS):    # Duration in seconds to flash the device's LED.  Use duration=0 to stop.
    nwkId = database.GetDeviceItem(devKey, "nwkId")
    ep = database.GetDeviceItem(devKey, "endPoints")
    if nwkId and ep:
        durationStr = format(int(durationS), 'X').zfill(4)
        queue.EnqueueCmd(devKey, ["AT+IDENTIFY:"+nwkId+","+ep+",0,"+durationStr, "DFTREP"]) # Identify for selected time

def SwitchOn(devKey):
    nwkId = database.GetDeviceItem(devKey, "nwkId")
    ep = database.GetDeviceItem(devKey, "endPoints")
    dimLevel = database.GetDeviceItem(devKey, "dimLevel")
    inClstr = database.GetDeviceItem(devKey, "inClusters") # For checking whether we have LevelCtrl
    if nwkId and ep:
        #database.UpdateLoggedItem(devKey, "State", "SwitchOn") # So that we can access it from the rules later
        devices.SetTempVal(devKey, "JustSentOnOff", "True")
        devices.SetTempVal(devKey, "ExpectOnOff", "SwitchOn")
        queue.EnqueueCmd(devKey, ["AT+RONOFF:"+nwkId+","+ep+",0,1", "OK"]) # Assume FFD if it supports OnOff cluster
        if zcl.Cluster.LevelCtrl in inClstr and dimLevel != 100:  # Queue up a dimming command if available and we're at a different dimness
            queue.EnqueueCmd(devKey, ["AT+LCMVTOLEV:"+nwkId+","+ep+",0,1,FE,0001", "OK"]) # Ensure fully bright ready to be turned on
            database.SetDeviceItem(devKey, "dimLevel", 100) # Assume the LevelCtrl command above works

def SwitchOff(devKey):
    nwkId = database.GetDeviceItem(devKey, "nwkId")
    ep = database.GetDeviceItem(devKey, "endPoints")
    if nwkId and ep:
        #database.UpdateLoggedItem(devKey, "State", "SwitchOff") # So that we can access it from the rules later
        devices.DelTempVal(devKey,"SwitchOff@") # Remove any pending "Off" events if we're turning the device off directly
        devices.SetTempVal(devKey, "JustSentOnOff", "True")
        devices.SetTempVal(devKey, "ExpectOnOff", "SwitchOff")
        queue.EnqueueCmd(devKey, ["AT+RONOFF:"+nwkId+","+ep+",0,0", "OK"]) # Assume FFD if it supports OnOff cluster
        database.SetDeviceItem(devKey, "dimLevel", 0) # Set dimness to 0

def Toggle(devKey):
    state = database.GetLatestEvent(devKey)
    log.debug("Asked to toggle, and old state is "+state)
    if state == "SwitchOn":
        SwitchOff(devKey)
    else:
        SwitchOn(devKey)
    #nwkId = database.GetDeviceItem(devKey, "nwkId")
    #ep = database.GetDeviceItem(devKey, "endPoints")
    #if nwkId and ep:
    #    devices.DelTempVal(devKey,"SwitchOff@") # Remove any pending "Off" events if we're handling the device directly
    #    devices.SetTempVal(devKey, "JustSentOnOff", "True")
    #    queue.EnqueueCmd(devKey, ["AT+RONOFF:"+nwkId+","+ep+",0", "OK"]) # Assume FFD if it supports OnOff cluster

def Dim(devKey, level):
    nwkId = database.GetDeviceItem(devKey, "nwkId")
    ep = database.GetDeviceItem(devKey, "endPoints")
    if nwkId and ep:
        if level > 1:  # Assume it's a percentage
            level = level / 100 # Convert to a fraction
        levelStr = format(int(level * 254), 'X').zfill(2)
        queue.EnqueueCmd(devKey, ["AT+LCMVTOLEV:"+nwkId+","+ep+",0,1,"+levelStr+",000A", "DFTREP"]) # Fade over 1 sec (in 10ths)
        if level == 0:
            SwitchOff(devKey)
        database.SetDeviceItem(devKey, "dimLevel", level*100) # Assume the LevelCtrl command above works

def Hue(devKey, hueDegree):
    nwkId = database.GetDeviceItem(devKey, "nwkId")
    ep = database.GetDeviceItem(devKey, "endPoints")
    if nwkId and ep:
        hueStr = format(int(float(hueDegree/360) * 254), 'X').zfill(2)
        queue.EnqueueCmd(devKey, ["AT+CCMVTOHUE:"+nwkId+","+ep+",0,"+hueStr+",00,0001", "DFTREP"]) # Fade over 100ms (in sec/10)

def Sat(devKey, satPercentage):
    nwkId = database.GetDeviceItem(devKey, "nwkId")
    ep = database.GetDeviceItem(devKey, "endPoints")
    if nwkId and ep:
        satStr = format(int(float(satPercentage/100) * 254), 'X').zfill(2)
        queue.EnqueueCmd(devKey, ["AT+CCMVTOSAT:"+nwkId+","+ep+",0,"+satStr+",0001", "DFTREP"]) # Fade over 100ms (in sec/10)

