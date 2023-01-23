#!/bin/python3
# weather.py

# Standard Python modules
import time
from urllib import request, parse
import json
from enum import Enum, auto
from datetime import datetime
import pprint
# App-specific Python modules
import log
import events
import variables
import config
import synopsis
import database

def EventHandler(eventId, eventArg):
    if events.ids.INIT == eventId:
        GetWeather() # Update weather immediately after start
    if events.ids.HOURS == eventId:
        GetWeather() # And every hour thereafter so that we only call OWM 24 times per day.  We're allowed up to 1000 for free if we want

def GetWeather():
    global forecastPeriod
    global cloudText, symSym
    global maxTemp, minTemp
    global maxWind, windDir
    SetUnknownWeather()
    owmApiKey = config.Get("owmApiKey")
    owmLat = config.Get("owmLat")
    owmLong = config.Get("owmLong")
    if (owmApiKey != None and owmLat != None and owmLong != None):
        req = request.Request("https://api.openweathermap.org/data/3.0/onecall?lat="+owmLat+"&lon="+owmLong+"&units=metric&exclude=minutely,hourly,alerts&appid="+owmApiKey) # Just use current and daily
        try:
            response = request.urlopen(req)
            jw = json.loads(response.read())
            log.debug("Weather:" + pprint.pformat(jw))
            # Get current weather
            outsideTemp = round(float(jw["current"]["temp"]), 2)
            cloudCover = round(float(jw["clouds"]["all"]), 2)
            windSpeed = round(float(jw["wind"]["speed"]) * 3.6, 2) # Windspeed in m/s to kph to 2 decimal places
            variables.Set("cloudCover_%", str(cloudCover), True)
            database.NewEvent(0, "Weather now "+str(cloudCover)+"% cloudy")
            variables.Set("outsideTemperature", str(outsideTemp), True)
            variables.Set("windSpeed_kph", str(windSpeed), True)
            # Get weather for whole day
            maxTemp = round(float(jw["daily"][0]["temp"]["max"]), 2)
            minTemp = round(float(jw["daily"][0]["temp"]["min"]), 2)
            cloudText = jw["daily"][0]["weather"][0]["description"]
            symSym = owmToSym(jw["daily"][0]["weather"][0]["icon"])
            maxWind = round(float(jw["daily"][0]["wind_speed"] * 3.6), 2)  # Convert from m/s to km/h
            windDir = round(float(jw["daily"][0]["wind_deg"]), 2)
            log.debug("maxTemp = " + str(maxTemp) + ", CloudText = " + str(cloudText) + ", maxWind = " + str(maxWind))
            forecastPeriod = "Day"
            events.Issue(events.ids.WEATHER)    # Tell system that we have a new weather report
        except Exception as e:
            synopsis.problem("Weather", "Problem @ " + str(datetime.now()) + " with exception " + str(e))
            SetUnknownWeather()
            database.NewEvent(0, "Weather Feed failed")

class Sym(Enum):
    Sun = auto()
    CloudWithSun = auto()
    Moon = auto()
    CloudWithMoon = auto()
    LightCloud = auto()
    DarkCloud = auto()
    LightRain = auto()
    HeavyRain = auto()
    Fog = auto()
    Snow = auto()
    Thunderstorms = auto()
    Unknown = auto()

def owmToSym(symbolVar):
    sym = {
        "01d":Sym.Sun,
        "02d":Sym.CloudWithSun,
        "01n":Sym.Moon,
        "02n":Sym.CloudWithMoon,
        "03d":Sym.LightCloud,
        "03n":Sym.LightCloud,
        "04d":Sym.DarkCloud,
        "04n":Sym.DarkCloud,
        "09d":Sym.LightRain,
        "09n":Sym.LightRain,
        "10d":Sym.HeavyRain,
        "10n":Sym.HeavyRain,
        "50d":Sym.Fog,
        "50n":Sym.Fog,
        "13d":Sym.Snow,
        "13n":Sym.Snow,
        "11d":Sym.Thunderstorms,
        "11n":Sym.Thunderstorms
        }
    return sym.get(symbolVar, Sym.Unknown)

def SetUnknownWeather():
    global forecastPeriod
    global cloudText, symSym
    global maxTemp, minTemp
    global maxWind, windDir, windText
    cloudText = ""
    forecastPeriod = "N/A"
    symSym = Sym.Unknown
    minTemp = 50.0 # Silly low temp
    maxTemp = -20.0 # Silly high temp
    maxWind = 0
    windDir = 0
    windText = ""



