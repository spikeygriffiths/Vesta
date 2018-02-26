# heating.py

import datetime
import time
import math
# App-specific modules
import zcl
import database
import devices
import queue
import events
import log
import iottime
import variables

thermoDevKey = None

def ParseCWShedule(eventArg):
    global thermoDevKey
    if eventArg[0] != "CWSCHEDULE" or len(eventArg) < 5:
        return
    devKey = devices.GetKey(eventArg[1])
    if devKey == None:
        return
    devices.NoteMsgDetails(devKey, eventArg)
    ep = eventArg[2]
    numSetpoints = int(eventArg[3], 16)
    dayOfWeekBitMap = int(eventArg[4], 16)
    dayOfWeekIndex = int(math.log(dayOfWeekBitMap, 2))
    dayOfWeek = iottime.GetDow(dayOfWeekIndex)    
    # Assume eventArg[5] holds "01" for heating schedule
    if len(eventArg) < 5+(2*numSetpoints): # Sanity check that we have all the bits of schedule we expect
        return
    newSchedule = []
    for index in range(0, numSetpoints):
        minutesSinceMidnight = eventArg[6+(index*2)] # Value in hex as number of minutes since midnight
        targetTemp = eventArg[6+(index*2)+1] # Value in hex as targetTemp in units of 1/100'C
        secs = int(minutesSinceMidnight, 16)*60
        timeOfDay = time.strftime("%H:%M", time.gmtime(secs))
        scheduleTemp = int(targetTemp, 16)/100
        newSchedule.append((timeOfDay, scheduleTemp))
    log.debug("Schedule for "+dayOfWeek+" is "+str(newSchedule))
    scheduleType = variables.Get("currentScheduleType")
    if scheduleType == None:
        scheduleType = "Winter"	# For now - ToDo could calculate season and use that
        variables.Set("currentScheduleType", scheduleType)
    database.SetSchedule(scheduleType, dayOfWeek, str(newSchedule)) # Update the database from the Thermostat/boiler device
    if dayOfWeek != "Sat":
        GetSchedule(thermoDevKey, iottime.GetDow(dayOfWeekIndex+1)) # Get next day's schedule

def GetSchedule(devKey, dayOfWeek="Sun"):  # Ask Thermostat/Boiler device for its schedule
    global thermoDevKey
    thermoDevKey = devKey
    nwkId = database.GetDeviceItem(devKey, "nwkId")
    if nwkId == None:
        return # Make sure it's a real device before continuing (it may have just been deleted)
    inClstr = database.GetDeviceItem(devKey, "inClusters") # Assume we have a list of clusters if we get this far
    if zcl.Cluster.Thermostat not in inClstr:
        return # Not a thermostat
    ep = database.GetDeviceItem(devKey, "endPoints")
    frameCtl="11"
    seqId="00"
    dayOfWeekIndex = iottime.GetDowIndex(dayOfWeek)
    dayBit = 2 ** dayOfWeekIndex # ** is "raise to the power".  Assumes dayOfWeek is a int where 0=Sunday, 1=Monday, etc.
    dayBitmask="{:02x}".format(dayBit) # bitmask as two digit hex 
    cmdRsp = ("AT+RAWZCL:"+nwkId+","+ep+","+zcl.Cluster.Thermostat+","+frameCtl+seqId+zcl.Commands.GetSchedule+dayBitmask+"01", zcl.Commands.GetScheduleRsp) #  Get heating(01) schedule
    queue.EnqueueCmd(devKey, cmdRsp)   # Queue up command for sending via devices.py
