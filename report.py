#!report.py

import events
import weather
import time
from datetime import datetime
import re # Regular Expression library for re.findall() to get targetTemp

import config # So that we can read power monitor
import devices # So that we can get devices.clampWattSeconds
import database
import variables
import log

def GetTimeInWords():
    numbers = ['Twelve', 'One', 'Two', 'Three', 'Four', 'Five', 'Six', 'Seven', 'Eight', 'Nine', 'Ten', 'Eleven', 'Twelve']
    hours = datetime.now().hour % 12
    minutes = datetime.now().minute
    if minutes >= 33: hours = hours + 1 # For "Quarter to ..."
    if hours > 12: hours = 1
    hourTxt = numbers[hours]
    if (minutes >= 58) or (minutes < 3):
        return hourTxt + " o\'clock"
    elif minutes < 8:
        return "Five past " + hourTxt
    elif minutes < 13:
        return "Ten past " + hourTxt
    elif minutes < 18:
        return "Quarter past " + hourTxt
    elif minutes < 23:
        return "Twenty past " + hourTxt
    elif minutes < 28:
        return "Twenty Five past " + hourTxt
    elif minutes < 33:
        return "Half past " + hourTxt
    elif minutes < 38:
        return "Twenty Five to " + hourTxt
    elif minutes < 43:
        return "Twenty to " + hourTxt
    elif minutes < 48:
        return "Quarter to " + hourTxt
    elif minutes < 53:
        return "Ten to " + hourTxt
    elif minutes < 58:
        return "Five to " + hourTxt
    return "Can't get here!"

def MakeText(id):
    if weather.forecastPeriod=="": return None;
    reportDict = dict()
    reportDict["target"] = id
    minutes = datetime.now().minute
    #if minutes % 2 == 0:
    #    reportDict["display"] = "off"
    #else:
    reportDict["display"] = "on" # For now at least
    reportDict["period"] = weather.forecastPeriod
    reportDict["icon"] = str(weather.symSym)[4:]
    reportDict["cloudText"] = weather.cloudText
    reportDict["maxTemp"] = str(round(weather.maxTemp))+"C"
    reportDict["minTemp"] = str(round(weather.minTemp))+"C"
    reportDict["windSpeed"] = str(round(weather.maxWind))
    reportDict["windDir"] = str(weather.windDir)
    reportDict["windText"] = weather.windText
    now = datetime.now()
    reportDict["timeDigits"] = str(now.strftime("%H:%M"))
    reportDict["timeText"] = GetTimeInWords()
    reportDict["dayOfWeekText"] = str(now.strftime("%A"))
    reportDict["dayOfMonthText"] = str(int(now.strftime("%d"))) # Use int() to remove leading zero
    reportDict["monthText"] = str(now.strftime("%B"))
    powerMonitorName = config.Get("PowerMonitor") # House power monitoring device
    if powerMonitorName != None:
        devKey = devices.FindDev(powerMonitorName)
        if devKey != None:
            powerW = database.GetLatestLoggedItem(devKey, "PowerReadingW")
            if powerW != None:
                reportDict["powerNow"] = str(powerW[0])
    energyToday = variables.Get("energyToday_kWh")
    if energyToday:
        reportDict["energyToday"] = energyToday
    tempMonitorName = config.Get("HouseTempDevice") # House temperature monitoring device
    if tempMonitorName != None:
        devKey = devices.FindDev(tempMonitorName)
        if devKey != None:
            houseTemp = database.GetLatestLoggedItem(devKey, "TemperatureCelsius")
            reportDict["houseTemp"] = '%.1f' % (houseTemp[0])
    targetTemp = variables.Get("TargetTemp")
    if targetTemp != None:
        reportDict["TargetTemp"] = targetTemp
    #log.debug("ReportDict for:" +id + "=" + str(reportDict)) # Already reported in WiFiServer.py
    return (str(reportDict))

