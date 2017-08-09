#!status.py

from datetime import datetime
import os
import log
import database
import presence

issues = {} # Empty dictionary at start

def BuildPage():
    log.debug("Building status.html...")
    html = open("status.html", "w")    # Create local temporary file, so we can send it via email, or copy it for Apache to serve up
    html.write("\n<html><head>")  # Blank line at start
    html.write("<style>")
    html.write(".good { color: green; }")
    html.write(".bad { color: red; }")
    html.write("</style>")
    html.write("</head><body>")
    html.write("<center><h1>IoT Status at " + datetime.now().strftime("%Y/%m/%d %H:%M:%S") + "</h1>")  # Put body here
    keyList = database.GetAllDevKeys()  # Get a list of all the device identifiers from the database
    for devKey in keyList:  # Element 0 is hub, rest are devices
        if database.GetDeviceItem(devKey, "nwkId") != "0000":  # Ignore hub
            availability = presence.GetFreq(devKey)
            if availability < 100:  # If device missing even only occasionally, tell user
                userName = database.GetDeviceItem(devKey, "userName")
                problem(userName+"_avail", userName+ " availabilty only "+str(availability)+"%")
    presence.ClearFreqs()
    if len(issues) > 0:
        for items in issues.values():
            html.write(items + "<br>")
        issues.clear()  # Clear the list, now that we've gone through it
    else:
        html.write("Everything OK!<br>")
    html.write("</body></html>")
    html.close()
    os.system("sudo cp status.html /var/www/html")  # So index.php can refer to it

def problem(key, value):
    issues[key] = value   # Add new, or update old, dictionary entry
    log.fault(key + ":" + value)
