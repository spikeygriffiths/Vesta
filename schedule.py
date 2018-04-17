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

overrideTimeoutMins = 0 # Not overriding initially
currentTargetTemp = 0 # Force schedule to be read in the first minute

def EventHandler(eventId, eventArg):
    global overrideTimeoutMins, currentTargetTemp
    if eventId == events.ids.MINUTES:
        name = config.Get("HeatingDevice")
        if name != None:
            heatingDevKey = devices.FindDev(name) # Get heating device every minute to allow for it changing
            if heatingDevKey != None:   # Check that we have a real heating device
                schedule = config.Get("HeatingSchedule")
                if schedule != None:
                    scheduledTargetTemp = GetTarget(schedule)
                    if scheduledTargetTemp != None: # We now have a heating device and a schedule to follow or override
                        if overrideTimeoutMins > 0:
                            overrideTimeoutMins = overrideTimeoutMins-1
                            if overrideTimeoutMins <= 0: # Just finished override
                                database.NewEvent(heatingDevKey, "Resume "+str(scheduledTargetTemp)+"'C") # For ActivityLog on web page
                                currentTargetTemp = heating.SetTargetTemp(heatingDevKey, scheduledTargetTemp)   # Resume schedule here
                            else: # Still overriding
                                if scheduledTargetTemp != currentTargetTemp: # Check whether schedule in heating device is about to change target
                                    database.NewEvent(heatingDevKey, "Overriding scheduled "+str(scheduledTargetTemp)+"'C with "+str(currentTargetTemp)+"C") # For ActivityLog on web page
                                    # Un-indent following line to force override temp once/min while overriding, rather than just at change
                                    heating.SetTargetTemp(heatingDevKey, currentTargetTemp)   # Re-Set target in heating device (since it's also running the schedule)
                        else: # Not overriding
                            if scheduledTargetTemp != currentTargetTemp:
                                database.NewEvent(heatingDevKey, "Scheduled "+str(scheduledTargetTemp)+"'C") # For ActivityLog on web page
                                #heating.SetTargetTemp(heatingDevKey, scheduledTargetTemp)   # Set target in heating device here.  (Not needed since it's running the schedule directly)
                                currentTargetTemp = scheduledTargetTemp
                    # else: No scheduled target
                # else: No HeatingSchedule
            # else: Despite having a name, there's no associated device
        # else: Ignore schedules and overrides if no named heating device

def Override(devKey, targetC, timeSecs):
    global overrideTimeoutMins, currentTargetTemp
    timeMins = int(int(timeSecs)/60)
    if timeMins > 0:
        overrideTimeoutMins = timeMins
        database.NewEvent(devKey, "Override "+str(targetC)+"'C") # For web page.  Update event log so I can check my schedule follower works
        currentTargetTemp = heating.SetTargetTemp(devKey, targetC)   # Set target in heating device here

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

