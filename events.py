#!events.py

# App-specific Python modules
import telegesis
import vesta
import devices
import rules
import commands
import variables
import wifiServer
import iottime
import database
import weather
import presence
import schedule

class ids:
    INIT = 0 # No arg
    SECONDS = 1 # Arg is elapsed time in seconds since last EVENT_SECONDS, currently 0.1
    TRIGGER = 2 # Arg is list, including nodeId in arg[1]
    BUTTON = 3  # Arg is list, including nodeId in arg[1] as well as button message in arg[0]
    CHECKIN = 4 # Arg is list, including nodeId in arg[1]
    RXMSG = 5 # Arg is list, direct from Telegesis
    RXERROR = 6 # Arg is decimal number indicating error
    RXOK = 7 # No arg.  We've received an OK and so that might be interesting if something's waiting for this
    DEVICE_ANNOUNCE = 8 # Arg is the whole response (devType, devEui, devNodeId)
    INFO = 9 # No arg, just print any useful info
    RX_TELEGESIS = 10   # Arg is line of raw Telegesis text
    MINUTES = 11 # No arg.  Issued at startup and once a minute thereafter
    PREINIT = 12 #  No arg.  Issued immediately before INIT
    HOURS = 13 # No arg.  Issued at startup and once an hour thereafter
    NEWDAY = 14 # No arg.  Issued once/day (at 1am for now)
    WEATHER = 15 # No arg.  Issued once/hour.  Various variables ("cloudCover", "rain", "windSpeed", "outsideTemperature") hold current weather
    TIMEOFDAY = 16 # Arg is string "morning", "lunchtime", etc.
    ALARM = 17 # Arg is string, one of "Arming", "Armed", Elevated", "Activated", "Disarmed" 
    RADIO_INFO = 18 # No arg, just displays info about the radio (channel, power, PAN id)
    NEWDEVICE = 19 # Arg is devKey, and only issued after the database has added the new device
    MULTISTATE = 20 # Arg is list, including nodeId in arg[1] and new presentValue in arg[0]
    SHUTDOWN = 21 # No arg.  Issued prior to rebooting, esp. to allow DB to commit

def Issue(eventId, eventArg=0):
    # Tell all interested parties about the new event
    vesta.EventHandler(eventId, eventArg)
    telegesis.EventHandler(eventId, eventArg)
    database.EventHandler(eventId, eventArg)
    variables.EventHandler(eventId, eventArg)
    devices.EventHandler(eventId, eventArg)
    iottime.EventHandler(eventId, eventArg)
    rules.EventHandler(eventId, eventArg)
    commands.EventHandler(eventId, eventArg)
    wifiServer.EventHandler(eventId, eventArg)
    weather.EventHandler(eventId, eventArg)
    presence.EventHandler(eventId, eventArg)
    schedule.EventHandler(eventId, eventArg)

