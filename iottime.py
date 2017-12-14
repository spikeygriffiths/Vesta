#!iottime.py

from datetime import datetime
from datetime import timedelta
from datetime import date
import calendar
from astral import Astral
import time
# App-specific modules
import events
import devices
import log
import rules
import variables
import database
import config
import synopsis

appStartTime = datetime.now()
oldMins = -1
oldHours = -1   # Force the first reading of time to change hour

def EventHandler(eventId, eventArg):
    global oldMins, oldHours
    if eventId == events.ids.INIT:
        SetDayInfo()
        SetSunTimes()
        if variables.Get("sunrise") != None:
            variables.Set("morning", variables.Get("sunrise"))
            variables.Set("evening", variables.Get("sunset"))   # Set up defaults until we get a weather report
            variables.Set("dark", str(GetDark()))
        rules.Run("trigger==appstart")
        database.NewEvent(0, "App started") # 0 is always hub
    elif eventId == events.ids.SECONDS:
        now = datetime.now()
        if now.minute != oldMins:
            events.Issue(events.ids.MINUTES)
            oldMins = now.minute # Ready for next time
    elif eventId == events.ids.MINUTES:
        now = datetime.now()
        if now.hour != oldHours:
            events.Issue(events.ids.HOURS)
            oldHours = now.hour # Ready for next time
        variables.Set("time", str(now.strftime("%H:%M")))
        rules.Run("trigger==time") # Run timed rules once per minute
        if variables.Get("sunrise") != None:
            CheckTimedRule("dawn", now) # Sky getting light before sunrise
            CheckTimedRule("sunrise", now) # Sun on horizon
            CheckTimedRule("morning", now) # Now proper daylight (depending on cloud)
            CheckTimedRule("evening", now)  # No longer proper daylight (depending on cloud)
            CheckTimedRule("sunset", now) # Sun on horizon
            CheckTimedRule("dusk", now) # Sky now getting dark after sunset
            dark = str(GetDark()) # Work out whether "dark" is True or False
            #log.debug("Old dark = " + variables.Get("dark") + " whereas new dark = " + dark)
            if dark != variables.Get("dark"):   # Compare with previous
                variables.Set("dark", dark)  # Update our idea of whether it's dark or light just now
                rules.Run("dark=="+variables.Get("dark"))
    if eventId == events.ids.HOURS:
        now = datetime.now()
        if now.hour == 0: # Midnight, time to calculate sunrise and sunset for new day
            events.Issue(events.ids.NEWDAY)
    if eventId == events.ids.NEWDAY:
        SetSunTimes()
        log.RollLogs() # Roll the logs, to avoid running out of disc space
        SetDayInfo()
        synopsis.BuildPage()  # Create status page, once/day, based upon reported problems during the previous day
        synopsis.clearProblems()

def GetDark():
    sunrise = datetime.strptime(variables.Get("sunrise"), "%H:%M")
    sunset = datetime.strptime(variables.Get("sunset"), "%H:%M")
    now = datetime.strptime(datetime.now().strftime("%H:%M"), "%H:%M")  # Just time of day
    cloudCover = variables.Get("cloudCover")
    if cloudCover != None:
        extraTime = int(cloudCover)    # Just take percentage cloudiness as minutes
        extraTime = extraTime + float(variables.Get("rain"))   # Any rain just makes it even darker (Measured in mm/3hr)
        extraTime = extraTime + float(variables.Get("snow"))   # Any snow just makes it even darker (Measured in mm/3hr)
    else:
        extraTime = 0   # No weather, so assume cloudless and dry
    morning = sunrise + timedelta(minutes=extraTime)    # The more cloud, the later it gets light in the morning
    evening = sunset - timedelta(minutes=extraTime) # The more cloud, the earlier it gets dark in the evening
    variables.Set("morning", morning.strftime("%H:%M"))
    variables.Set("evening", evening.strftime("%H:%M"))   # Set up variables accordingly
    return not(IsTimeBetween(morning, now, evening)) # True if dark, False if light

def SetDayInfo():
    today = date.today()
    dayOfWeek = today.weekday()
    variables.Set("dayOfWeek", calendar.day_name[dayOfWeek]) # To allow different rules on different days of the week
    if dayOfWeek < 5:
        variables.Set("weekend","false")
    else:
        variables.Set("weekend", "true")
    variables.Set("dayOfMonth", str(today.day))
    variables.Set("month", str(today.month))

def SetSunTimes():
    cityName = config.Get("cityName")
    if cityName != None:
        a = Astral()
        a.solar_depression= "civil"
        city = a[cityName]
        sun = city.sun(date=datetime.now(), local=True)
        variables.Set("dawn", str(sun['dawn'].strftime("%H:%M")))
        variables.Set("sunrise", str(sun['sunrise'].strftime("%H:%M")))
        variables.Set("sunset", str(sun['sunset'].strftime("%H:%M")))
        variables.Set("dusk", str(sun['dusk'].strftime("%H:%M")))

def Get(item):
    if ":" not in item: # If named item rather than HH:MM timestamp
        item = variables.Get(item)    # Get time of day from variable (eg sunrise, etc.)
    return datetime.strptime(item, "%H:%M")

def CheckTimedRule(name, now):
    if variables.Get(name) == now.strftime("%H:%M"):
        rules.Run("time=="+name) # Special rule for sunrise, sunset, etc.

def IsTimeBetween(startTime, nowTime, endTime):
    if startTime <= nowTime <= endTime:
       return True
    else:
       return False

def Sanitise(val):  # Assume val is a string containing a hour:minute time
    if ":" in val:  # Check for colon before sanitising time stamp
        try:
            timeOfDay = datetime.strptime(val, "%H:%M") # Convert to time
        except:
            synopsis.problem("TimedRule", "Bad time in Rule containing '" + val)
            return "BadTime"    # Must return something
        return "\""+timeOfDay.strftime("%H:%M")+"\"" # Normalise timestamp (cope with leading zeros)
    else:
        return val  # Return original string if no colon
