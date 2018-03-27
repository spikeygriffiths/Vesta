#!schedule.py

from datetime import datetime
# App-specific modules
import events
import devices
import log
import variables
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
            if overrideTimeoutMins == 0:
                target = GetTarget("HeatingSchedule")
                database.NewEvent(devKey, "Resume after override "+str(target)) # For web page.  Update event log so I can check my schedule follower works
                heating.SetTargetTemp(heatingDevKey, target)   # Resume schedule here
        else:
            if heatingDevKey != None:   # and running schedule remotely...
                scheduleType = config.Get("HeatingSchedule")
                dayOfWeek = variables.Get("dayOfWeek")
                scheduleStr = database.GetSchedule(scheduleType, dayOfWeek)
                now = datetime.strptime(datetime.now().strftime("%H:%M"), "%H:%M")  # Just time of day
                for item in scheduleStr:
                    if item[0] == now:
                        target = item[1]
                        database.NewEvent(devKey, "Scheduled "+str(target)) # For web page.  Update event log so I can check my schedule follower works
                        #heating.SetTargetTemp(heatingDevKey, target)   # Set target in heating device here

def Override(devKey, targetC, timeSecs):
    global overrideTimeoutMins
    timeMins = int(timeSecs/60)
    if timeMins > 0:
        database.NewEvent(devKey, "Override to "+str(targetC)) # For web page.  Update event log so I can check my schedule follower works
        overrideTimeoutMins = timeMins
        SetTarget(devKey, targetC)   # Set target in heating device here

def GetTarget(scheduleName):
    scheduleType = config.Get(scheduleName)
    dayOfWeek = variables.Get("dayOfWeek")
    scheduleStr = database.GetSchedule(scheduleType, dayOfWeek) # Get schedule for today
    timeOfDay = datetime.strptime(datetime.now().strftime("%H:%M"), "%H:%M")
    for item in scheduleStr:    # Each item consists of a time and a target
        if target == None:
            target = item[1]    # Make sure have a target even early in the morning, before first change
        if item[0] > timeOfDay:
            return target   # Stop as soon as we find the current slot
        else:
            target = item[1]    # Remember last target
        return target   # If we reach the end of today's schedule, then assume our time is after last change, so use last target

