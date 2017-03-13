#!/bin/python3
# weather.py

# Standard Python modules
import pyowm
# App-specific Python modules
import log
import events

owm = pyowm.OWM("590c17ed39950e5bc6648c3f83918987")  # My API Key

def EventHandler(eventId, eventArg):
    global owm
    if eventId == events.ids.HOURS: # Get weather once/hour
        obs = owm.weather_at_place("Cambridge,UK")  # My location
        w = obs.get_weather()
        cloudCover = w.get_clouds() # Percentage cloud cover
        events.Issue(events.ids.CLOUD_COVER, cloudCover)    # Tell system, so rules can advance sunset accordingly
        log.log("Cloud cover now is " + str(cloudCover) + "%")
        outsideTemp = w.get_temperature("celsius")["temp"] # Outside temperature in celsius
        events.Issue(events.ids.OUTSIDE_TEMP, outsideTemp)    # Tell system
        log.log("Outside temperature now is " + str(outsideTemp) + "'C")

