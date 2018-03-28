#!schedule.py

from datetime import datetime
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
                target = GetTarget("HeatingSchedule")
                if target != None:
                    database.NewEvent(heatingDevKey, "Resume to "+str(target)+"'C") # For web page.  Update event log so I can check my schedule follower works
                    heating.SetTargetTemp(heatingDevKey, target)   # Resume schedule here
                else:
                    database.NewEvent(heatingDevKey, "No target to resume to!")
        else:
            if heatingDevKey != None:   # and running schedule remotely...
                heating.GetTargetTemp(heatingDevKey) # Ensure we keep track of remote device's target
                heating.GetSourceTemp(heatingDevKey) # ...and source temperature's
                scheduleType = config.Get("HeatingSchedule")
                if scheduleType == None:
                    log.fault("No HeatingSchedule!")
                    return
                dayOfWeek = iottime.GetDow(datetime.today().weekday())
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
                timeOfDay = datetime.strptime(datetime.now().strftime("%H:%M"), "%H:%M")  # Just time of day
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
    scheduleType = config.Get(scheduleName)
    timeOfDay = datetime.strptime(datetime.now().strftime("%H:%M"), "%H:%M")
    dayOfWeek = iottime.GetDow(datetime.today().weekday())
    scheduleStr = database.GetSchedule(scheduleType, dayOfWeek) # Get schedule for today
    if scheduleStr == None:
        log.fault("No schedule found for "+scheduleType+" on "+dayOfWeek)
        return None
    log.debug("Schedule for today("+dayOfWeek+") is "+scheduleStr)
    try:
        scheduleList = eval(scheduleStr)
    except:
        log.fault("Can't turn "+scheduleStr+" into a list")
        return None # Bad list from database
    target = None
    numSetpoints = len(scheduleList)
    for index in range(0, numSetpoints):
        timeTemp = scheduleList[index]  # Get each time & temp from schedule
        timeStr = timeTemp[0]
        tempStr = timeTemp[1]
        if target == None:
            target = tempStr    # Make sure have a target even early in the morning, before first change
        if iottime.MakeTime(timeStr) > iottime.MakeTime(timeOfDay):
            return tempStr   # Stop as soon as we find the current slot
        else:
            target = tempStr    # Remember last target
        return target   # If we reach the end of today's schedule, then assume our time is after last change, so use last target

