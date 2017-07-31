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
import status

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
        rules.Run("trigger==hubstart")
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
        rules.Run("time=="+now.strftime("%H:%M")) # Run timed rules once per minute with time of date
        if variables.Get("sunrise") != None:
            CheckTimedRule("dawn", now) # Sky getting light before sunrise
            CheckTimedRule("sunrise", now) # Sun on horizon
            CheckTimedRule("morning", now) # Now proper daylight (depending on cloud)
            CheckTimedRule("evening", now)  # No longer proper daylight (depending on cloud)
            CheckTimedRule("sunset", now) # Sun on horizon
            CheckTimedRule("dusk", now) # Sky now getting dark after sunset
        status.BuildPage()  # Create status page, probably once/hour?
    if eventId == events.ids.HOURS:
        now = datetime.now()
        if now.hour == 0: # Midnight, time to calculate sunrise and sunset for new day
            events.Issue(events.ids.NEWDAY)
    if eventId == events.ids.NEWDAY:
            SetSunTimes()
            log.RollLogs() # Roll the logs, to avoid running out of disc space
            SetDayInfo()
    if eventId == events.ids.WEATHER:
        if variables.Get("sunrise") != None:    # Can only use weather if we know sunrise & sunset
            now = datetime.now()
            nowTime = datetime.strptime(now.strftime("%H:%M"), "%H:%M")
            extraTime = int(variables.Get("cloudCover"))    # Just take percentage cloudiness as minutes
            extraTime = extraTime + float(variables.Get("rain"))   # Any rain just makes it even darker (Measured in mm/3hr)
            extraTime = extraTime + float(variables.Get("snow"))   # Any snow just makes it even darker (Measured in mm/3hr)
            sunrise = datetime.strptime(variables.Get("sunrise"), "%H:%M")
            morning = sunrise + timedelta(minutes=extraTime)    # The more cloud, the later it gets light in the morning
            oldMorning = variables.Get("morning")
            if oldMorning != None:
                oldMorning = datetime.strptime(oldMorning, "%H:%M")
                if morning<nowTime and oldMorning>nowTime:  # If the new morning is before now and the old morning was after, then make sure we still issue the "morning" rule
                    morning = now + timedelta(minutes=1) # Set morning to be in the next minute if the clouds are clearing away
            variables.Set("morning", str(morning.strftime("%H:%M")))
            sunset = datetime.strptime(variables.Get("sunset"), "%H:%M")
            evening = sunset - timedelta(minutes=extraTime) # The more cloud, the earlier it gets dark in the evening
            oldEvening = variables.Get("evening")
            if oldEvening != None:
                oldEvening = datetime.strptime(oldEvening, "%H:%M")
                if evening<nowTime and oldEvening>nowTime:  # If the new evening is before now and the old evening was after, then make sure we still issue the "evening" rule
                    evening = now + timedelta(minutes=1) # Set evening to be in the next minute if the clouds are building up
            variables.Set("evening", str(evening.strftime("%H:%M")))

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

