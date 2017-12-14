#!/bin/python3
# weather.py

# Standard Python modules
import pyowm
from datetime import datetime
# App-specific Python modules
import log
import events
import variables
import config
import synopsis
import database

owm = None
apiKey = None
location =  None

def EventHandler(eventId, eventArg):
    global owm, apiKey, location
    if eventId == events.ids.HOURS: # Get weather once/hour
        if owm == None:
            apiKey = config.Get("owmApiKey")
            location =  config.Get("owmLocation")
        if (apiKey != None and location != None):
            owm = pyowm.OWM(apiKey) # My API key
            try:
                obs = owm.weather_at_place(location)  # My location
            except:
                database.NewEvent(0, "Weather Feed failed!")
                synopsis.problem("Weather", "Feed failed @ " + str(datetime.now()))
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
            database.NewEvent(0, "Weather now "+str(cloudCover)+"% cloudy")
            events.Issue(events.ids.WEATHER)    # Tell system that we have a new weather report

