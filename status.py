#!status.py

from datetime import datetime
import os
# 
import log
import database
import presence
import iottime
import vesta

issues = {} # Empty dictionary at start

def BuildPage():
    upTime = datetime.now() - iottime.appStartTime
    log.debug("Building status.html...")
    email = open("status.email", "w")    # Create text file for emailing.  Could put HTML inside here once I work out how!
    html = open("status.html", "w")    # Create local temporary file, so we can copy it for Apache to serve up
    html.write("\n<html><head>")  # Blank line at start
    html.write("<style>.good { color: green; }.bad { color: red; }</style>")
    html.write("</head><body>")
    html.write("<center><h1>Vesta Status at " + datetime.now().strftime("%Y/%m/%d %H:%M:%S") + "</h1>")  # Put body here
    email.write("Vesta Status at " + datetime.now().strftime("%Y/%m/%d %H:%M:%S")+"\n\n");
    html.write("Vesta v" + vesta.GetVersion()+"<br>")
    email.write("Vesta v" + vesta.GetVersion()+"\n")
    html.write("Uptime: %d days, %.2d:%.2d" % (upTime.days, upTime.seconds//3600, (upTime.seconds//60)%60)+"<br>") # Cribbed from "uptime" command
    email.write("Uptime: %d days, %.2d:%.2d" % (upTime.days, upTime.seconds//3600, (upTime.seconds//60)%60)+"\n") # Cribbed from "uptime" command
    if upTime.seconds > 3600:
        keyList = database.GetAllDevKeys()  # Get a list of all the device identifiers from the database
        for devKey in keyList:  # Element 0 is hub, rest are devices
            if database.GetDeviceItem(devKey, "nwkId") != "0000":  # Ignore hub
                availability = presence.GetFreq(devKey)
                if availability < 100:  # If device missing even only occasionally, tell user
                    userName = database.GetDeviceItem(devKey, "userName")
                    problem(userName+"_avail", userName+ " availability only "+str(availability)+"%")
        presence.ClearFreqs()
        if len(issues) > 0:
            for items in issues.values():
                html.write(items + "<br>")
                email.write(items + "\n")
            issues.clear()  # Clear the list, now that we've gone through it
        else:
            html.write("Everything OK!<br>")
            email.write("Everything OK!\n")
    else: # Insufficient running time to make a sensible status page
        html.write("(Insufficient running time to make a sensible status page)<br>")
        email.write("(Insufficient running time to make a sensible status page)\n")
    html.write("</body></html>")
    html.close()
    email.close()
    os.system("sudo cp status.html /var/www/html/vesta")  # So vesta.php can refer to it.  Will overrwrite any previous status

def problem(key, value):
    issues[key] = value   # Add new, or update old, dictionary entry
    log.fault(key + ":" + value)
