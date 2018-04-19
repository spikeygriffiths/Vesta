#!variables.py

import random
from datetime import datetime
# App-specific Python modules
import log
import events
import database

def EventHandler(eventId, eventArg):
    global varList
    if eventId == events.ids.SECONDS:
        away = database.GetAppState("away")
        if away == None:
            away = "False"    # Assume at home if we don't know any better
            database.SetAppState("away", away)  # Ensure database has our same default
            Set("away", away)  # Keep our variable in sync with the value from the database, so now user can update the db via the web and we'll know...
        oldAway = Get("away")
        if oldAway == None:
            oldAway = "Unknown" # Force update
        if oldAway != away:
            log.debug("Away state has changed from "+oldAway+" to "+away)
            if away == "False":
                database.NewEvent(0, "Arrived Home")
            else:
                database.NewEvent(0, "Gone Away")
            Set("away", away)  # Keep our variable in sync with the value from the database, so now user can update the db via the web and we'll know...

def Set(name, value, force=False):
    if force==True or Get(name) != value:  # Only update value if it has changed, unless forced
        log.debug("Variable \""+name+"\" gets "+value)
        database.SetVar(name, value)

def Del(name):
    database.DelVar(name)
    
def Get(name):  # Get value associated with name
    if name.lower() == "rand":
        return random.random() * 100    # Could return random.randrange(0,101) to give an integer percentage
    if "." in name:
        dotPos = name.find(".")
        foreName = name[:dotPos]
        postName = name[dotPos+1:]
        devKey = database.GetDevKey("userName", foreName)
        if devKey: # Check that name is a device name
            return database.GetLatestLoggedValue(devKey, postName) # To get latest temperature, power, etc.        
    return database.GetVarVal(name)

def GetTime(name):  # Get time when value associated with name was last updated
    return database.GetVarTime(name)

