#config.py

from pathlib import Path
# App-specific modules
import log

configFilename = "config.txt"

def Get(item, default=None):
    configFile = Path(configFilename)
    if configFile.is_file():
        with open(configFilename) as config:
            for line in config:
                if line[0] != "#":  # Ignore comment lines
                    lineList = line.split("=") # Make each line into a list consisting of item on left side and value on right side of "="
                    if lineList[0].strip() == item: # Strip leading & trailing spaces and do a case-insensitive match
                        value = lineList[1].splitlines()[0] # Discard trailing newline
                        value = value.strip()   # Discard leading or trailing spaces
                        #log.debug("Matched:"+lineList[0]+ "with value:"+value)
                        return value
    if default != None:
        log.debug("Missing variable from " + configFilename + " : " + item + "  Using default of " + default)
    else:
        log.debug("Missing variable from " + configFilename + " : " + item + "  No default")
    return default  # If we get all through the config file without finding a match, use default value
 
