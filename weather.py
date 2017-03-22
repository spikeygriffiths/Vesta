#!/bin/python3
# weather.py

# Standard Python modules
import pyowm
# App-specific Python modules
import log
import events
import variables

owm = pyowm.OWM("590c17ed39950e5bc6648c3f83918987")  # My API Key

def EventHandler(eventId, eventArg):
    global owm
    if eventId == events.ids.HOURS: # Get weather once/hour
        try:
            obs = owm.weather_at_place("Cambridge,UK")  # My location
        except:
            log.fault("Couldn't get weather")
            return
        w = obs.get_weather()
        cloudCover = w.get_clouds() # Percentage cloud cover
        variables.Set("cloudCover", str(cloudCover))
        outsideTemp = w.get_temperature("celsius")["temp"] # Outside temperature in celsius
        variables.Set("outsideTemperature", str(outsideTemp))
        windSpeed = w.get_wind()["speed"]
        variables.Set("windSpeed", str(windSpeed))
        rain = w.get_rain()
        if rain != {}:
            rain = rain["3h"]   # Rain volume in last 3 hours.  Unknown units, may be ml(?)
        else:
            rain = 0    # No rain
        variables.Set("rain", str(rain))
        snow = w.get_snow()
        if snow != {}:
            snow = snow["3h"]   # Snow volume in last 3 hours.  Unknown units, may be ml(?)
        else:
            snow = 0    # No snow
        variables.Set("snow", str(snow))
        events.Issue(events.ids.WEATHER, windSpeed)    # Tell system
