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

dayStart = datetime.strptime("08:00:00", "%H:%M:%S")
dayEnd = datetime.strptime("16:00:00", "%H:%M:%S")
eveStart = dayEnd  #datetime.strptime("16:00:00", "%H:%M:%S")
eveEnd = datetime.strptime("23:00:00", "%H:%M:%S")
def EventHandler(eventId, eventArg):
    global updateWeather, forecastPeriod
    if events.ids.INIT == eventId:
        forecastPeriod = "" # Until we know better
        updateWeather = time.time() # Update weather immediately after start
    if events.ids.SECONDS == eventId:
        if time.time() >= updateWeather:
            GetWeatherNow()
            GetWeatherForecast()
            updateWeather = time.time() + 600 # Only get weather forecast every 10 mins

def GetWeatherNow():
    variables.Set("cloudCover", "30", True) # Default to 30% cloudcover to give half an hour either side of sunrise & sunset for dark=true
    owmApiKey = config.Get("owmApiKey")
    owmLat = config.Get("owmLat")
    owmLong = config.Get("owmLong")
    if (owmApiKey != None and owmLat != None and owmLong != None):
        #url = "https://api.openweathermap.org/data/2.5/weather?q="+owmLocation+"&mode=xml&appid="+owmApiKey
        url = "https://api.openweathermap.org/data/3.0/onecall?lat="+owmLat+"&lon="+owmLong+"&units=metric&exclude=minutely,hourly,daily,alerts&appid="+owmApiKey
        log.debug("Getting weather using:"+url)
        req = request.Request(url)
        try:
            response = request.urlopen(req)
            rawWeather = response.read()
            log.debug("Weather now==" + rawWeather.decode("utf-8"))
            jw = json.loads(rawWeather)
            outsideTemp = round(float(jw["current"]["temp"]), 2)
            cloudCover = round(float(jw["clouds"]["all"]), 2)
            windSpeed = round(float(jw["wind"]["speed"]) * 3.6, 2) # Windspeed in m/s to kph to 2 decimal places
            variables.Set("cloudCover", str(cloudCover), True)
            database.NewEvent(0, "Weather now "+str(cloudCover)+"% cloudy")
            variables.Set("outsideTemperature", str(outsideTemp), True)
            variables.Set("windSpeed", str(windSpeed), True)
            events.Issue(events.ids.WEATHER)    # Tell system that we have a new weather report
        except Exception as e:
            synopsis.problem("Weather", "Feed failed @ " + str(datetime.now()) + " with exception " + str(e))
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

def SetUnknownForecast():
    global cloudText, symSym
    global maxTemp, minTemp
    global maxWind, windDir
    cloudText = ""
    symSym = Sym.Unknown
    minTemp = 50.0 # Silly low temp
    maxTemp = -20.0 # Silly high temp
    maxWind = 0
    windDir = 0

def GetWeatherForecast():
    global forecastPeriod
    global cloudText, symSym
    global maxTemp, minTemp
    global maxWind, windDir
    forecastPeriod = "N/A"
    owmApiKey = config.Get("owmApiKey")
    owmLat = config.Get("owmLat")
    owmLong = config.Get("owmLong")
    #req = request.Request("https://api.openweathermap.org/data/2.5/forecast?q="+owmLocation+"&mode=xml&appid="+owmApiKey)
    req = request.Request("https://api.openweathermap.org/data/3.0/onecall?lat="+owmLat+"&lon="+owmLong+"&units=metric&exclude=current,minutely,hourly,alerts&appid="+owmApiKey) # Just use daily
    try:
        response = request.urlopen(req)
        jw = json.loads(response.read())
        log.debug("Daily weather:" + pprint.pformat(jw))
        maxTemp = round(float(jw["daily"][0]["temp"]["max"]), 2)
        minTemp = round(float(jw["daily"][0]["temp"]["min"]), 2)
        log.debug("maxTemp = " + str(maxTemp))
        cloudText = jw["daily"][0]["weather"][0]["description"]
        symSym = owmToSym(jw["daily"][0]["weather"][0]["icon"])
        log.debug("CloudText = " + str(cloudText))
        maxWind = round(float(jw["daily"][0]["wind_speed"] * 3.6), 2)  # Convert from m/s to km/h
        windDir = round(float(jw["daily"][0]["wind_deg"]), 2)
        log.debug("maxWind = " + str(maxWind))
        forecastPeriod = "Day"
    except Exception as e:
        synopsis.problem("Weather", "Problem @ " + str(datetime.now()) + " with exception " + str(e))
        SetUnknownForecast()


