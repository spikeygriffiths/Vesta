#!iottime.py

from datetime import datetime
from astral import Astral
# App-specific modules
import events
import devices
import log
import hubapp
import rules
import variables

if __name__ == "__main__":
    hubapp.main()

oldMins = 0

def EventHandler(eventId, eventArg):
    global oldMins
    if eventId == events.ids.INIT:
        SetSunTimes()
        rules.Run("trigger==hubstart")
        devices.SetSynopsis("IoT Hub started at", str(datetime.now()))
    if eventId == events.ids.SECONDS:
        now = datetime.now()
        if now.minute != oldMins:
            oldMins = now.minute # Ready for next time
            rules.Run("time=="+now.strftime("%H:%M")) # Run timed rules once per minute with time of date
            CheckTimedRule("dawn", now)
            CheckTimedRule("sunset", now)
            CheckTimedRule("sunrise", now)
            CheckTimedRule("dusk", now)
            if now.minute == 0 and now.hour == 1: # 1am, time to calculate sunrise and sunset for new day 
                SetSunTimes()
                log.NewLog() # Roll the logs, to avoid running out of disc space
                
def SetSunTimes():
    cityName = "London"
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
        item = variables.Get(item)    # Get time from variable (eg sunrise, etc.)
    return datetime.strptime(item, "%H:%M")

def CheckTimedRule(name, now):
    if variables.Get(name) == now.strftime("%H:%M"):
        rules.Run("time=="+name) # Special rule for sunrise, sunset, etc.

