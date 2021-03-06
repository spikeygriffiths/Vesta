#config.py

# App-specific modules
import database
import log

def Get(item, default=None):
    value = database.GetConfig(item)
    if value != None:
        return value
    if default != None:
        log.debug("Missing config item : " + item + "  Using default of " + default)
        database.SetConfig(item, default)   # Make sure we create a default if it doesn't exist
    else:
        log.debug("Missing config item : " + item + "  No default")
    return default  # If we get all through the config file without finding a match, use default value
 
