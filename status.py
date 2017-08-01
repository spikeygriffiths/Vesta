#!status.py

from datetime import datetime
import os
import log
import database
#import presence

def BuildPage():
    log.debug("Building status.html...")
    html = open("status.html", "w")    # Create local temporary file, so we can send it via email, or copy it for Apache to serve up
    html.write("\n<html><head>")  # Blank line at start
    html.write("<style>")
    html.write(".good { color: green; }")
    html.write(".bad { color: red; }")
    html.write("</style>")
    html.write("</head><body>")
    html.write("<center><h1>IoT Status</h1>")  # Put body here
    keyList = database.GetAllDevKeys()  # Get a list of all the device identifiers from the database
    for devKey in keyList:  # Hub and devices
        devName = database.GetDeviceItem(devKey, "userName")
        if "SED"== database.GetDeviceItem(devKey, "devType"):
            battLevel, battTime = database.GetStatus(devKey, "battery")
            if battLevel == None:
                battLevel = -1  # Use this to mean "No battery level"
        else:
            battLevel = 101  # Use this to mean "No battery needed"
        sigLevel, sigTime = database.GetStatus(devKey, "signal")
        if sigLevel == None:
            sigLevel = -1   # Use this to mean "No signal detected"
        statusStr = ""
        if battLevel != 101:
            if battLevel >= 10:
                statusStr = statusStr + "<line class=\"good\"> Good Battery (" + str(battLevel) + "%)</line>"
            else:
                statusStr = statusStr + "<line class=\"bad\"> <b>Low Battery</b> (" + str(battLevel) + "%)</line>"
        elif battLevel == -1:  # Use this to mean "No battery level"
                statusStr = statusStr + "<line class=\"bad\"> <b>No Battery</b> reading!</line>"
        if sigLevel > 95:
            statusStr = statusStr + "<line class=\"good\"> Excellent Radio signal (" + str(sigLevel) + "%)</line>"
        elif sigLevel > 75:
            statusStr = statusStr + "<line class=\"good\"> Good Radio signal (" + str(sigLevel) + "%)</line>"
        elif sigLevel != -1:
            statusStr = statusStr + "<line class=\"bad\"> <b>Poor Radio</b> signal (" + str(sigLevel) + "%)</line>"
        if statusStr != "":
            html.write(devName + ":" + statusStr + "<br>")        
    html.write("<br></center>Page built at " + datetime.now().strftime("%Y/%m/%d %H:%M:%S"))
    html.write("</body></html>")
    html.close()
    os.system("sudo cp status.html /var/www/html")  # So index.php can refer to it

