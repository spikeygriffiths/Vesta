#!/bin/python3
# weather.py

# Standard Python modules
import time
from urllib import request, parse
import xml.etree.ElementTree as ET
from enum import Enum, auto
from datetime import datetime
# App-specific Python modules
import log
import events
import variables
import config
import synopsis
import database

def EventHandler(eventId, eventArg):
    global updateWeather
    if events.ids.INIT == eventId:
        updateWeather = time.time() # Update weather immediately after start
    if events.ids.SECONDS == eventId:
        if time.time() >= updateWeather:
            GetWeatherNow()
            GetWeatherForecast()
            updateWeather = time.time() + 600 # Only get weather forecast every 10 mins

def GetWeatherNow():
    variables.Set("cloudCover", "30", True) # Default to 30% cloudcover to give half an hour either side of sunrise & sunset for dark=true
    owmApiKey = config.Get("owmApiKey")
    owmLocation =  config.Get("owmLocation")
    if (owmApiKey != None and owmLocation != None):
        url = "https://api.openweathermap.org/data/2.5/weather?q="+owmLocation+"&mode=xml&appid="+owmApiKey
        log.debug("Getting weather using:"+url)
        req = request.Request(url)
        try:
            response = request.urlopen(req)
            rawWeather = response.read()
            log.debug("Weather now==" + rawWeather.decode("utf-8"))
            root = ET.fromstring(rawWeather.decode("utf-8"))
            for child in root:
                log.debug("Found child:"+str(child.tag)+" in XML")
                if child.tag=="temperature":
                    outsideTemp = round((float(child.attrib["value"]) - 273.15), 2) # Convert Kelvin to Celsius to 2 decimal places
                    variables.Set("outsideTemperature", str(outsideTemp), True)
                if child.tag == "clouds":
                    cloudCover = child.attrib["value"] # Percentage cloud cover
                    variables.Set("cloudCover", str(cloudCover), True)
                    database.NewEvent(0, "Weather now "+str(cloudCover)+"% cloudy")
                for detail in child:
                    #log.debug("Found detail:"+str(detail.tag)+" in XML")
                    if child.tag == "wind" and detail.tag == "speed":
                        windSpeed = round((float(detail.attrib["value"]) * 3.6),2) # Windspeed in m/s to kph to 2 decimal places
                        variables.Set("windSpeed", str(windSpeed), True)
                        #if detail.tag == "main":
                        #    if detail.attribute == "drizzle":
                        #rain = 0    # No rain
                        #variables.Set("rain", str(rain), True)
            events.Issue(events.ids.WEATHER)    # Tell system that we have a new weather report
        except Exception as inst:
            database.NewEvent(0, "Weather Feed failed with error "+inst)
            synopsis.problem("Weather", "Feed failed @ " + str(datetime.now())+" with error "+inst)


dayStart = datetime.strptime("08:00:00", "%H:%M:%S")
dayEnd = datetime.strptime("16:00:00", "%H:%M:%S")
eveStart = dayEnd  #datetime.strptime("16:00:00", "%H:%M:%S")
eveEnd = datetime.strptime("23:00:00", "%H:%M:%S")

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

def GetWorstWeather(detail):
    global cloudText, symSym, severestGroup, severestSub
    global maxTemp, minTemp
    global maxWind, windText, windDir
    if detail.tag == "symbol":
        symbolText = detail.attrib["name"] # eg "Broken clouds"
        symbolNumber = int(detail.attrib["number"]) # Group 2xx=Thunderstorm, 3xx=Drizzle, 5xx=Rain, 6xx=Snow, 7xx=Atmosphere, 800=Clear, 8xx=Clouds
        symbolVar = detail.attrib["var"]
        log.debug("("+str(symbolNumber)+")"+symbolText+","+str(symbolVar)+"=="+str(owmToSym(symbolVar)))
        symbolGroup = int(symbolNumber/100)
        symbolSub = symbolNumber % 100
        if symbolGroup==severestGroup:
            if symbolSub>severestSub:
                severestSub=symbolSub
                symSym=owmToSym(symbolVar)
                cloudText=symbolText
        else:
            if symbolGroup==2: # Thunderstorms
                severestGroup=symbolGroup # Nothing beats thunderstorms!
                severestSub=symbolSub
                symSym=owmToSym(symbolVar)
                cloudText=symbolText
            elif symbolGroup==3: # Drizzle
                if severestGroup==8: # Drizzle beats clouds
                    severestGroup=symbolGroup
                    severestSub=symbolSub
                    symSym=owmToSym(symbolVar)
                    cloudText=symbolText
            elif symbolGroup==5: # Rain
                if severestGroup==8 or severestGroup==2: # Rain beats clouds & drizzle
                    severestGroup=symbolGroup
                    severestSub=symbolSub
                    symSym=owmToSym(symbolVar)
                    cloudText=symbolText
            elif symbolGroup==6:
                if severestGroup==8 or severestGroup==2 or severestGroup==5: # Snow beats clouds, drizzle or rain
                    severestGroup=symbolGroup
                    severestSub=symbolSub
                    symSym=owmToSym(symbolVar)
                    cloudText=symbolText
    if detail.tag == "temperature":
        low = float(detail.attrib["min"]) - 273.15 # Convert Kelvin to Celsius
        high = float(detail.attrib["max"]) - 273.15
        log.debug("low temp {0:.1f}".format(low)+" high {0:.1f}".format(high))
        if low < minTemp:
            minTemp = low
        if high > maxTemp:
            maxTemp = high
    if detail.tag == "windSpeed":
        speed = float(detail.attrib["mps"]) * 3.6 # Convert mps to kph
        if speed > maxWind:
            maxWind = speed
            windText = detail.attrib["name"]
    if detail.tag == "windDirection":
        dir = round(float(detail.attrib["deg"]))
        windDir = dir # Might want to try averaging wind direction, rather than just getting last one?

def SetDefaultForecast():
    global cloudText, symSym, severestSymbol, severestGroup, severestSub
    global maxTemp, minTemp
    global maxWind, windText, windDir
    severestSymbol = 800 # 800, Clear sky by default
    severestGroup = int(severestSymbol/100)
    severestSub = severestSymbol % 100
    cloudText = "Clear sky"
    symSym = owmToSym("01d") # Assume clear day sky
    minTemp = 50.0 # Silly low temp
    maxTemp = -20.0 # Silly high temp
    maxWind = 0

def SetUnknownForecast():
    global cloudText, symSym, severestSymbol, severestGroup, severestSub
    global maxTemp, minTemp
    global maxWind, windText, windDir
    severestSymbol = 800 # 800, Clear sky by default
    severestGroup = int(severestSymbol/100)
    severestSub = severestSymbol % 100
    cloudText = "N/A"
    symSym = Sym.Unknown
    minTemp = 50.0 # Silly low temp
    maxTemp = -20.0 # Silly high temp
    maxWind = 0
    windText = "N/A"
    windDir = 0

def GetForecastSlot(forecastSlot):
    for detail in forecastSlot:
        GetWorstWeather(detail) # Need to compare symbolNumber vs previous one to get most extreme weather
    # Now use severestGroup & severestSub to make a Sym

def GetWeatherForecast():
    global forecastPeriod
    global cloudText, symSym, severestSymbol, severestGroup, severestSub
    global maxTemp, minTemp
    global maxWind, windText, windDir
    forecastPeriod = "N/A"
    SetDefaultForecast()
    owmApiKey = config.Get("owmApiKey")
    owmLocation =  config.Get("owmLocation")
    req = request.Request("https://api.openweathermap.org/data/2.5/forecast?q="+owmLocation+"&mode=xml&appid="+owmApiKey)
    try:
        response = request.urlopen(req)
        root = ET.fromstring(response.read())
        for child in root:
            if child.tag == "forecast":
                for forecastSlot in child:
                    #print(startTime.attrib["from"])
                    start = (datetime.strptime(forecastSlot.attrib["from"],"%Y-%m-%dT%H:%M:%S"))
                    if start.date()==datetime.now().date():
                        if datetime.now().time() < dayEnd.time():
                            if start.time() > dayStart.time() and start.time() < dayEnd.time():
                                forecastPeriod = "Day"
                                GetForecastSlot(forecastSlot)
                        else:
                            if start.time() > eveStart.time() and start.time() < eveEnd.time():
                                forecastPeriod = "Eve"
                                GetForecastSlot(forecastSlot)
    except:
        SetUnknownForecast()
    if forecastPeriod!="N/A":
        severestSymbol = severestGroup * 100 + severestSub


