#!iottime.py

from datetime import datetime
from datetime import timedelta
from datetime import date
import calendar
#import astral
from astral.sun import sun
from astral import LocationInfo
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
import myqueue
import telegesis
import zcl

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
        telegesis.SetTime() # Set time up for HA devices to synchronise to
        myqueue.EnqueueCmd(0, ["AT+SETATR:000A,0001,05", "OK"]) # Set Master clock and timezone bits on CICIE
        myqueue.EnqueueCmd(0, ["AT+TIMERD", "OK"]) # Set CICIE as time server
    elif eventId == events.ids.SECONDS:
        now = datetime.now()
        if now.minute != oldMins:
            events.Issue(events.ids.MINUTES, now.minute)
            oldMins = now.minute # Ready for next time
    elif eventId == events.ids.MINUTES:
        now = datetime.now()
        if now.hour != oldHours:
            events.Issue(events.ids.HOURS, now.hour)
            oldHours = now.hour # Ready for next time
        variables.Set("time", str(now.strftime("%H:%M")))
        rules.Run("time=="+ str(now.strftime("%H:%M"))) # Run timed rules once per minute
        rules.Run("trigger==time") # Run timed rules once per minute
        # Could alter above to rules.Run("trigger==minute")
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
                rules.Run("dark=="+variables.Get("dark"))  # This will also delete the variable afterwards
                variables.Set("dark", dark)  # Re-instate the variable after the rule has deleted it
    if eventId == events.ids.HOURS:
        # Could add rules.Run("trigger==hour")
        if eventArg == 0: # Midnight, time to calculate sunrise and sunset for new day
            events.Issue(events.ids.NEWDAY)
        if eventArg == 4: # Re-synch Telegesis clock to local time at 4am every day to cope with DST
            telegesis.SetTime() # Set time up for HA devices to synchronise to
    if eventId == events.ids.NEWDAY:
        # Could add rules.Run("trigger==day")
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
    else:
        extraTime = 0   # No weather, so assume cloudless and dry
    if extraTime < 30:
        extraTime = 30 # Minimum of half an hour of evening before sunset
    morning = sunrise + timedelta(minutes=extraTime)    # The more cloud, the later it gets light in the morning
    evening = sunset - timedelta(minutes=extraTime) # The more cloud, the earlier it gets dark in the evening
    oldMorning = variables.Get("morning")  # if time is between variables.Get("morning") and newly calculated morning, then rules.Run("time==morning")
    oldEvening = variables.Get("evening")  # if time is between variables.Get("evening") and newly calculated evening, then rules.Run("time==evening")
    if IsTimeBetween(morning, now, oldMorning):
        rules.Run("time==morning")
    if IsTimeBetween(evening, now, oldEvening):
        rules.Run("time==evening")
    variables.Set("morning", morning.strftime("%H:%M"), True)
    variables.Set("evening", evening.strftime("%H:%M"), True)   # Set up variables accordingly
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
        city = LocationInfo(cityName)
        s = sun(city.observer, date=datetime.now())
        variables.Set("dawn", str(s['dawn'].strftime("%H:%M")), True)
        variables.Set("sunrise", str(s['sunrise'].strftime("%H:%M")), True)
        variables.Set("sunset", str(s['sunset'].strftime("%H:%M")), True)
        variables.Set("dusk", str(s['dusk'].strftime("%H:%M")), True)

def Get(item):
    if ":" not in item: # If named item rather than HH:MM timestamp
        item = variables.Get(item)    # Get time of day from variable (eg sunrise, etc.)
    if item == None:
        item = "00:00" # Null items become midnight
    return datetime.strptime(item, "%H:%M")

def CheckTimedRule(name, now):
    if variables.Get(name) == now.strftime("%H:%M"):
        rules.Run("time=="+name) # Special rule for sunrise, sunset, etc.

def MakeTime(timeOfDay): # Accepts string or timestamp and returns timestamp as time of day or None if there's a problem
    if isinstance(timeOfDay, str) == False:
        try: # Assume it's a timestamp
            timeOfDay = timeOfDay.strftime("%H:%M")
        except:
            return None # Couldn't convert to time string, so wasn't time after all
    try: # Ought to be a string holding a time now, so try and convert it to a timestamp 
        return datetime.strptime(timeOfDay, "%H:%M") # Convert to time
    except:
        return None # Couldn't convert to time

def IsTimeBetween(startTime, nowTime, endTime):
    startTime = MakeTime(startTime)
    nowTime = MakeTime(nowTime)
    endTime = MakeTime(endTime)
    if startTime != None and nowTime != None and endTime != None:
        if startTime < endTime: # Make sure start is earlier than end
           return startTime <= nowTime <= endTime
        else: # allow for end being earlier than start
           return endTime <= nowTime <= startTime
    else:
        return False # Bad timestamps always fail

def Sanitise(val):  # Assume val is a string containing a hour:minute time
    timeOfDay = MakeTime(val)
    if timeOfDay == None:
        synopsis.problem("TimedRule", "Bad time in Rule containing '" + val)
        return None    # Must return something
    return "\""+timeOfDay.strftime("%H:%M")+"\"" # Normalise timestamp (cope with leading zeros)

def GetDowIndex(dayOfWeek): # Get int from string, where "Sun"=>0, "Mon"=>1, etc.
    days = dict(zip(calendar.day_abbr, range(7)))
    return (days[dayOfWeek]+1)%7 # Convert Mon-Sun (Python default) to Sun-Sat (ZCL default)

def GetDow(dowIndex): # Get string from int, where 0=>"Sun", 1=>"Mon", etc.
   dowIndex = dowIndex-1
   if dowIndex == -1:
       dowIndex = 6 # Simple modulus arithmetic (%7) won't wrap for negative numbers
   return calendar.day_abbr[dowIndex%7]

def GetDaysOfWeek():
    return dict(zip(calendar.day_abbr, range(7)))

def FromZigbee(zigSecs):    # Return timestamp given Zigbee time
    unixTime = zigSecs + 946684800  # Convert to seconds since 1/Jan/1970
    return datetime.fromtimestamp(unixTime).strftime("%Y-%m-%d %H:%M:%S")

def ToZigbee(unixSecs):
    return unixSecs - 946684800  # Convert to seconds since 1/Jan/2000

def GetTime(devKey):
    telegesis.TxReadDevAttr(devKey, zcl.Cluster.Time, zcl.Attribute.LocalTime) # Create string and queue it up for sending
