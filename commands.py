#!commands.py

# Command Line Interpreter module for Vesta

# Standard Python modules
import cmd
import readline
import os
import sys
import select
import socket
from pathlib import Path
from pprint import pprint # Pretty print for devs list
from datetime import datetime
from datetime import timedelta
from subprocess import call
# App-specific Python modules
import devices
import devcmds
import queue
import events
import telegesis
import variables
import rules
import vesta
import log
import iottime
import database
import synopsis

sck = ""
cliSck = ""
sckLst = []

def EventHandler(eventId, eventArg):
    global sckLst, sck, cliSck
    if eventId == events.ids.INIT:
        sck = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # Create socket
        sck.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sck.setblocking(0) # accept() is no longer blocking
        port = 12345
        try:
            sck.bind(('', port))    # Listen on all available interfaces
        except OSError as err: # "OSError: [Errno 98] Address already in use"
            database.NewEvent(0, "Socket bind failed with " + err.args[1]) # 0 is always hub
            vesta.Reboot()
        sck.listen(0)
        sckLst = [sck]
    if eventId == events.ids.SECONDS:
        if select.select([sys.stdin], [], [], 0)[0]:
            cmd = sys.stdin.readline()
            if cmd:
                Commands().onecmd(cmd)
        rd, wr, er = select.select(sckLst, [], [], 0)
        for s in rd:
            if s is sck:
                cliSck, addr = sck.accept()
                sckLst.append(cliSck)
                #log.debug("New connection from web page!")
            else:
                try:
                    cmd = cliSck.recv(100)
                except OSError as err:  # OSError: [Errno 9] Bad file descriptor"
                    database.NewEvent(0, "Web command failed with " + err.args[1]) # 0 is always hub
                    cmd = ""    # No command if there was a failure                
                if cmd:
                    cmd = cmd.decode()
                    log.debug("Got cmd \""+ cmd+"\" from web page")
                    sys.stdout = open("cmdoutput.txt", "w") # Redirect stdout to file
                    Commands().onecmd(cmd)
                    sys.stdout = sys.__stdout__ # Put stdout back to normal (will hopefully also close the file)
                    f = open("cmdoutput.txt", "r")
                    cmdOut = f.read()
                    cliSck.send(str.encode(cmdOut))
                    call("rm cmdoutput.txt", shell=True) # Remove cmd output after we've used it
                else:
                    #log.debug("Closing socket")
                    cliSck.close()
                    if cliSck in sckLst:
                        sckLst.remove(cliSck)
    # End of Command EventHandler

class Commands(cmd.Cmd):
    
    def do_info(self, line):
        """info
        Displays useful information"""
        events.Issue(events.ids.INFO)

    def do_uptime(self, line):
        """uptime
        Shows time app has been running"""
        upTime = datetime.now() - iottime.appStartTime
        print("%d days, %.2d:%.2d" % (upTime.days, upTime.seconds//3600, (upTime.seconds//60)%60))  # Used by web page

    def do_version(self, line):
        """version
        Shows version of this app"""
        print("Vesta v" + vesta.GetVersion())

    def do_radio(self, item):
        """radio
        Shows info about the radio (channel, power, PAN id)"""
        events.Issue(events.ids.RADIO_INFO) # Used by web page for hub info

    def do_vars(self, item):
        """vars [item]
        Show all variables, or just variables that contain item"""
        if item == "":
            vars = variables.varList
            vars.sort() # Alphabetic by name, to make it easier to search by eye
            pprint (vars)
        else:
            itemisedList = []
            for v in variables.varList:
                if item.lower() in v[0].lower():
                    itemisedList.append(v)
            # end for loop
            try:
                pprint(sorted(itemisedList, key = lambda val: val[1]))
            except:
                pprint(itemisedList)    # If it's not sortable (mix of floats and strs), then just print it in any order

    def do_set(self, line):
        """set name value
        Set named variable to value"""
        if " " in line:
            argList = line.split(" ")
            name = argList[0]
            val = argList[1]
            variables.Set(name, val)
        else:
            variables.Del(line)

    def do_open(self, line):
        """open
        Opens network (for 60s) to allow new device to join"""
        queue.EnqueueCmd(0, ["AT+PJOIN", "OK"])

    def do_identify(self, line):
        """identify name seconds
        Sends identify command to named device.  Use 0 seconds to stop immediately"""
        argList = line.split()
        if len(argList) >= 2:
            devKey = devices.FindDev(argList[0])
            if devKey != None:
                timeS = int(argList[1])
                devcmds.Identify(devKey, timeS)
        else:
            log.fault("Insufficient Args")

    def do_toggle(self, devId):
        """toggle name
        Sends toggle on/off command to named device"""
        devKey = devices.FindDev(devId)
        if devKey != None:
            devcmds.Toggle(devKey)

    def do_dim(self, line):
        """dim name percentage
        Sends level command to named device"""
        argList = line.split()
        if len(argList) >= 2:
            percentage = int(argList[1])
            devKey = devices.FindDev(argList[0])
            if devKey != None:
                devcmds.Dim(devKey, percentage)
        else:
            log.fault("Insufficient Args")

    def do_hue(self, line):
        """hue name hue
        Sends ColorCtrl command to named device, where 0<hue<360"""
        argList = line.split()
        if len(argList) >= 2:
            hue = int(argList[1])
            devKey = devices.FindDev(argList[0])
            if devKey != None:
                devcmds.Hue(devKey, hue)
        else:
            log.fault("Insufficient Args")

    def do_sat(self, line):
        """sat name sat
        Sends ColorCtrl command to named device, where 0<sat<100"""
        argList = line.split()
        if len(argList) >= 2:
            sat = int(argList[1])
            devKey = devices.FindDev(argList[0])
            if devKey != None:
                devcmds.Sat(devKey, sat)
        else:
            log.fault("Insufficient Args")

    def do_at(self, line):
        """at cmd
        Sends AT command to Telegesis stick"""
        queue.EnqueueCmd(0, ["AT"+line, "OK"])

    def do_devat(self, line):
        """devat name cmd
        Sends AT command to named device"""
        argList = line.split()
        if len(argList) >= 2:
            cmd = argList[1]
            devKey = devices.FindDev(argList[0])
            if devKey != None:
                queue.EnqueueCmd(devKey, ["AT"+cmd, "OK"])

    def do_removeDevice(self, devId):
        """removeDevice id
        Tells device to leave the network and remove it from the database"""
        devKey = devices.FindDev(devId)
        if devKey != None:
            devices.Remove(devKey)

    def do_rolllog(self, line):
        """rolllog
        Rolls the logs - automatically done at midnight"""
        log.RollLogs()

    def do_synopsis(self, line):
        """synopsis
        Constructs synopsis.html page"""
        synopsis.BuildPage()

