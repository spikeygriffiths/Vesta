#config.py

# App-specific modules
import database
import log

configFilename = "config.txt"

def Get(item, default=None):
    value = database.GetConfig(item)
    if value != None:
        return value
    if default != None:
        log.debug("Missing variable from " + configFilename + " : " + item + "  Using default of " + default)
    else:
        log.debug("Missing variable from " + configFilename + " : " + item + "  No default")
    return default  # If we get all through the config file without finding a match, use default value
 
