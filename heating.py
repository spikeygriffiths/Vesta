# heating.py

import datetime
import time
import math
import calendar
calendar.setfirstweekday(calendar.SUNDAY)
# App-specific modules
import zcl
import database
import devices
import queue
import events
import log

def ParseCWShedule(eventArg):
    if eventArg[0] != "CWSCHEDULE" or len(eventArg) < 5:
        return
    devKey = devices.GetKey(eventArg[1])
    if devKey == None:
        return
    devices.NoteMsgDetails(devKey, eventArg)
    ep = eventArg[2]
    numSetpoints = int(eventArg[3], 16)
    dayOfWeekBitMap = int(eventArg[4], 16)
    dayOfWeek = int(math.log(dayOfWeekBitMap, 2))    
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
    log.debug("Schedule for "+calendar.day_abbr[dayOfWeek]+" is "+str(newSchedule))

def GetSchedule(devKey):
    nwkId = database.GetDeviceItem(devKey, "nwkId")
    if nwkId == None:
        return # Make sure it's a real device before continuing (it may have just been deleted)
    inClstr = database.GetDeviceItem(devKey, "inClusters") # Assume we have a list of clusters if we get this far
    if zcl.Cluster.Thermostat not in inClstr:
        return # Not a thermostat
    ep = database.GetDeviceItem(devKey, "endPoints")
    frameCtl="11"
    seqId="00"
    dayOfWeek="01" # bitmask, so bit 0=Sunday, bit 1=Monday, etc. 
    cmdRsp = ("AT+RAWZCL:"+nwkId+","+ep+","+zcl.Cluster.Thermostat+","+frameCtl+seqId+zcl.Commands.GetSchedule+dayOfWeek+"01", zcl.Commands.GetScheduleRsp) #  Get heating(01) schedule
    queue.EnqueueCmd(devKey, cmdRsp)   # Queue up command for sending via devices.py
