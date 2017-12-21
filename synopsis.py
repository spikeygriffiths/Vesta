#!synopsis.py

from datetime import datetime
import os
import glob
# Application-specific modules
import log
import database
import presence
import iottime
import config
import vesta

issues = {} # Empty dictionary at start

def BuildPage():
    upTime = datetime.now() - iottime.appStartTime
    absUrl = config.Get("vestaURL", "")
    log.debug("Building status page")
    txt = open("synopsis.txt", "w")    # Create text file for txt
    html = open("synopsis.html", "w")    # Create local html file, so we can copy it for Apache to serve up, or mail directly
    html.write("\n<html><head>")  # Blank line at start
    html.write("</head><body>")
    html.write("<center><h1>Vesta Status</h1>")
    txt.write("Vesta Status\n\n");
    writeLine("At " + datetime.now().strftime("%H:%M") + " on " + datetime.now().strftime("%Y/%m/%d"), html, txt)
    writeLine("Uptime: %d days, %.2d:%.2d" % (upTime.days, upTime.seconds//3600, (upTime.seconds//60)%60), html, txt) # Cribbed from "uptime" command
    writeLine("", html, txt)    # Just newline
    keyList = database.GetAllDevKeys()  # Get a list of all the device identifiers from the database
    noProblems = True
    for devKey in keyList:  # Element 0 is hub, rest are devices
        if database.GetDeviceItem(devKey, "nwkId") != "0000":  # Ignore hub
            availability = presence.GetAvailability(devKey)
            if availability != "":  # If device missing even only occasionally, tell user (Entry string means "fine")
                noProblems = False
                writeLine(availability, html, txt)
    dbSize = database.GetFileSize() 
    if (dbSize / len(keyList)) > (30 * 1024):   # Arbitrary limit of 30K per device
        noProblems = False
        problem("dbSize", "Database file size is " + "{0:.2f}".format(dbSize/(1024 * 1024)) + "MB which is " + "{0:.0f}".format((dbSize / len(keyList)) / 1024) + "KB per device")
    errList = glob.glob("/home/pi/Vesta/*_err.log")   # Get list of all error logs
    numLogs = len(errList)
    if numLogs:
        noProblems = False
        if numLogs == 1:
            problem("error_logs", "1 error log")
        else:
            problem("error_logs", str(numLogs) + " error logs")
    if len(issues) > 0:
        noProblems = False
        for items in issues.values():
            writeLine(items, html, txt)
    if noProblems:
        writeLine("Everything OK!", html, txt)
    writeLine("", html, txt)    # Just newline
    writeLine("(Vesta v" + vesta.GetVersion()+")", html, txt)
    html.write("<br><center><a href=\"" + absUrl + "/vesta/index.php\"><img src=\"" + absUrl + "/vesta/vestaLogo.png\" width=32 height=32 title=\"Home\"></a>")
    html.write("</body></html>")
    html.close()
    txt.close()
    os.system("sudo cp synopsis.html /var/www/html/vesta")  # So vesta.php can refer to it.  Will overrwrite any previous status

def writeLine(string, html, txt):
    html.write(string+"<br>")
    txt.write(string+"\n")

def problem(key, value):
    issues[key] = value   # Add new, or update old, dictionary entry
    log.fault(key + ":" + value)


def clearProblems():    # Called at midnight each day
    issues.clear()  # Clear the list, now that we've gone through it

