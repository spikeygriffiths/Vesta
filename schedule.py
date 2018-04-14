#!schedule.py

from datetime import datetime
from datetime import date
import time
# App-specific modules
import events
import devices
import log
import variables
import iottime
import database
import config
import zcl
import heating

overrideTimeoutMins = None
heatingDevKey = None

def EventHandler(eventId, eventArg):
    global overrideTimeoutMins, heatingDevKey
    if eventId == events.ids.INIT:
        overrideTimeoutMins = 0
        name = config.Get("HeatingDevice")
        if name != None:
            heatingDevKey = devices.FindDev(name)
    elif eventId == events.ids.MINUTES:
        if overrideTimeoutMins > 0:
            overrideTimeoutMins = overrideTimeoutMins-1
            if overrideTimeoutMins == 0 and heatingDevKey != None:
                schedule = config.Get("HeatingSchedule")
                if schedule != None:
                    target = GetTarget(schedule)
                    if target != None:
                        database.NewEvent(heatingDevKey, "Resume to "+str(target)+"'C") # For web page.  Update event log so I can check my schedule follower works
                        heating.SetTargetTemp(heatingDevKey, target)   # Resume schedule here
                    else:
                        database.NewEvent(heatingDevKey, "No target to resume to!")
                else:
                    database.NewEvent(heatingDevKey, "No HeatingSchedule!")
        else:
            if heatingDevKey != None:   # and running schedule remotely...
                heating.GetTargetTemp(heatingDevKey) # Ensure we keep track of remote device's target
                heating.GetSourceTemp(heatingDevKey) # ...and source temperature's
                scheduleType = config.Get("HeatingSchedule")
                if scheduleType == None:
                    log.fault("No HeatingSchedule!")
                    return
                dayOfWeek = iottime.GetDow(date.today().isoweekday() % 7) # So that Sun=0, Mon=1, etc.
                scheduleStr = database.GetSchedule(scheduleType, dayOfWeek)
                if scheduleStr == None:
                    log.debug("No schedule found for "+scheduleType)
                    return
                try:
                    scheduleList = eval(scheduleStr)
                except:
                    log.fault("Can't turn "+scheduleStr+" into a list")
                    return  # Bad list from database
                numSetpoints = len(scheduleList)
                timeOfDay = datetime.now().strftime("%H:%M")  # Just time of day
                for index in range(0, numSetpoints):
                    timeTemp = scheduleList[index]  # Get each time & temp from schedule
                    timeStr = timeTemp[0]
                    tempStr = timeTemp[1]
                    if iottime.MakeTime(timeStr) == iottime.MakeTime(timeOfDay):
                        database.NewEvent(heatingDevKey, "Scheduled "+str(tempStr)+"'C") # For web page.  Update event log so I can check my schedule follower works
                        #heating.SetTargetTemp(heatingDevKey, tempStr)   # Set target in heating device here

def Override(devKey, targetC, timeSecs):
    global overrideTimeoutMins
    timeMins = int(int(timeSecs)/60)
    if timeMins > 0:
        database.NewEvent(devKey, "Override to "+str(targetC)+"'C") # For web page.  Update event log so I can check my schedule follower works
        overrideTimeoutMins = timeMins
        heating.SetTargetTemp(devKey, targetC)   # Set target in heating device here

def GetTarget(scheduleName):
    timeOfDay = datetime.now().strftime("%H:%M")
    dayOfWeek = iottime.GetDow(date.today().isoweekday() % 7) # So that Sun=0, Mon=1, etc.
    scheduleStr = database.GetSchedule(scheduleName, dayOfWeek) # Get schedule for today
    if scheduleStr == None:
        log.fault("No schedule found for "+scheduleType+" on "+str(dayOfWeek))
        return None
    log.debug("Resuming using schedule for today("+str(dayOfWeek)+") is "+scheduleStr)
    try:
        scheduleList = eval(scheduleStr)
    except:
        log.fault("Bad schedule - Can't turn "+scheduleStr+" into a list")
        return None # Bad list from database
    target = 7 # Should really be the last scheduled temperature from the previous day's schedule
    numSetpoints = len(scheduleList)
    for index in range(0, numSetpoints):
        timeTemp = scheduleList[index]  # Get each time & temp from schedule
        timeStr = timeTemp[0]
        tempStr = timeTemp[1]
        #log.debug("Checking whether "+str(timeOfDay)+" is greater than "+str(timeStr))
        if iottime.MakeTime(timeOfDay) >= iottime.MakeTime(timeStr):
            target = tempStr    # Remember last target
    return target   # If we reach the end of today's schedule, then assume our time is after last change, so use last target

