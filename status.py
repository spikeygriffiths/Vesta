#!status.py

from datetime import datetime
import os
import log
import database
#import presence

def BuildPage():
    log.debug("Building status.html...")
    html = open("status.html", "w")    # Create local temporary file, so we can send it via email, or copy it for Apache to serve up
    html.write("\n")  # Blank line at start
    html.write("<html><head>")
    # Put head here
    html.write("</head><body>")
    html.write("<center><h1>Status</h1>")  # Put body here
    keyList = database.GetAllDevKeys()  # Get a list of all the device identifiers from the database
    for devKey in keyList:  # Hub and devices
        devName = database.GetDeviceItem(devKey, "userName")
        if "SED"== database.GetDeviceItem(devKey, "devType"):
            battLevel, battTime = database.GetStatus(devKey, "battery")
            if battLevel != None:
                html.write(devName+ " Battery " + str(battLevel) + "%" + " at " + str(battTime) + "<br>")
    html.write("<br></center>Built at :" + str(datetime.now()))
    html.write("</body></html>")
    html.close()
    os.system("sudo cp status.html /var/www/html")  # So index.php can refer to it

