# heating.py

from datetime import datetime
import time
import math
# App-specific modules
import zcl
import database
import devices
import myqueue
import events
import log
import iottime
import variables
import config
import telegesis

thermoDevKey = None

def NewSchedule(name):
    days = iottime.GetDaysOfWeek()  # Get list of days of the week
    newSchedStr = "[('06:30', 20.0), ('08:30', 16.0), ('17:30', 20.0), ('20:00', 7.0)]"
    for day in days:
        database.SetSchedule(name, day, newSchedStr) # Create new schedule in database

def DelSchedule(name):
    database.DelSchedule(name)

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
    username = database.GetDeviceItem(devKey, "userName")
    log.debug("Schedule from "+username+" for "+dayOfWeek+" is "+str(newSchedule))
    scheduleType = username  # was config.Get("HeatingSchedule", "Heating")
    database.SetSchedule(scheduleType, dayOfWeek, str(newSchedule)) # Update the database from the Thermostat/boiler device

def GetSchedule(devKey):  # Ask Thermostat/Boiler device for its schedule
    global thermoDevKey
    thermoDevKey = devKey
    days = iottime.GetDaysOfWeek()  # Get list of days of the week
    for day in days:
        GetDaySchedule(devKey, day) # Get each day's schedule

def GetDaySchedule(devKey, dayOfWeek="Sun"):  # Ask Thermostat/Boiler device for its schedule
    global thermoDevKey
    nwkId = CheckThermostat(devKey)
    if nwkId == None:
        return # Make sure it's a real thermostat device before continuing
    thermoDevKey = devKey
    ep = database.GetDeviceItem(devKey, "endPoints")
    frameCtl="11"
    seqId="00"
    dayOfWeekIndex = iottime.GetDowIndex(dayOfWeek)
    dayBit = 2 ** dayOfWeekIndex # ** is "raise to the power".  Assumes dayOfWeek is a int where 0=Sunday, 1=Monday, etc.
    cmdRsp = ("AT+RAWZCL:"+nwkId+","+ep+","+zcl.Cluster.Thermostat+","+frameCtl+seqId+zcl.Commands.GetSchedule+"{:02X}".format(dayBit)+"01", "CWSCHEDULE") #  Get heating(01) schedule
    myqueue.EnqueueCmd(devKey, cmdRsp)   # Queue up command for sending via devices.py

def SetSchedule(devKey, scheduleType="Heating"): # Tell Thermostat/boiler device about this schedule
    global thermoDevKey
    thermoDevKey = devKey
    days = iottime.GetDaysOfWeek()  # Get list of days of the week
    for day in days:
       SetDaySchedule(devKey, scheduleType, day)

def SetDaySchedule(devKey, scheduleType="Heating", dayOfWeek="Sun"):
    nwkId = CheckThermostat(devKey)
    if nwkId == None:
        return # Make sure it's a real thermostat device before continuing
    ep = database.GetDeviceItem(devKey, "endPoints")
    frameCtl="11"
    seqId="00"
    dayOfWeekIndex = iottime.GetDowIndex(dayOfWeek)
    log.debug("From "+dayOfWeek+" get value of "+str(dayOfWeekIndex))
    dayBit = 2 ** dayOfWeekIndex # ** is "raise to the power".  Assumes dayOfWeek is a int where 0=Sunday, 1=Monday, etc.
    scheduleStr = database.GetSchedule(scheduleType, dayOfWeek)
    try:
        scheduleList = eval(scheduleStr)
    except:
        return  # Bad list from database
    numSetpoints = len(scheduleList)
    scheduleStr = ""
    for index in range(0, numSetpoints):
        timeTemp = scheduleList[index]  # Get each time & temp from schedule
        timeStr = timeTemp[0]
        tempStr = timeTemp[1]
        time = datetime.strptime(timeStr, "%H:%M")
        minsSinceMidnight = (time.hour*60)+time.minute
        htonMins = telegesis.ByteSwap(minsSinceMidnight)
        htonTemp = telegesis.ByteSwap(int(float(tempStr)*100))
        scheduleStr = scheduleStr + "{:04X}".format(htonMins)
        scheduleStr = scheduleStr + "{:04X}".format(htonTemp)
    cmdRsp = ("AT+RAWZCL:"+nwkId+","+ep+","+zcl.Cluster.Thermostat+","+frameCtl+seqId+zcl.Commands.SetSchedule+"{:02X}".format(numSetpoints)+"{:02X}".format(dayBit)+"01"+scheduleStr, "CWSCHEDULE") #  Set heating(01) schedule
    myqueue.EnqueueCmd(devKey, cmdRsp)   # Queue up command for sending via devices.py

def CheckThermostat(devKey):
    nwkId = database.GetDeviceItem(devKey, "nwkId")
    if nwkId == None:
        return None # Make sure it's a real device before continuing (it may have just been deleted)
    inClstr = database.GetDeviceItem(devKey, "inClusters") # Assume we have a list of clusters if we get this far
    if zcl.Cluster.Thermostat not in inClstr:
        return None # Not a thermostat
    return nwkId

def GetSourceTemp(devKey):
    telegesis.TxReadDevAttr(devKey, zcl.Cluster.Thermostat, zcl.Attribute.LocalTemp) #  Get Thermostat's source temp

def RptTemp(devKey, temp): # This could be renamed as SetSourceTemp()
    centiTemp = format(int(float(temp)*100), 'X').zfill(4)
    telegesis.TxReportAttr(devKey, zcl.Cluster.Temperature, zcl.Attribute.Celsius, zcl.AttributeTypes.Sint16, centiTemp) #  Report measured temperature to a device (eg thermostat)

def SetTargetTemp(devKey, temp):
    centiTemp = format(int(float(temp)*100), 'X').zfill(4)
    telegesis.TxWriteAttr(devKey, zcl.Cluster.Thermostat, zcl.Attribute.OccupiedHeatingSetPoint, zcl.AttributeTypes.Sint16, centiTemp) #  Set Thermostat's source temp
    return temp # So we can say current = SetTargetTemp(temp)

def GetTargetTemp(devKey):
    telegesis.TxReadDevAttr(devKey, zcl.Cluster.Thermostat, zcl.Attribute.OccupiedHeatingSetPoint) #  Get Thermostat's target temp

