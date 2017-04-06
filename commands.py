#!commands.py

# Command Line Interpreter module for hubapp

# Standard Python modules
import cmd
import readline
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
import events
import telegesis
import variables
import rules
import hubapp
import log
import iottime
import database

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
        sck.bind(('', port))    # Listen on all available interfaces
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
                cmd = cliSck.recv(100)
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
                    log.debug("Closing socket")
                    cliSck.close()
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

    def do_radio(self, item):
        """radio
        Shows info about the radio (channel, power, PAN id)"""
        events.Issue(events.ids.RADIO_INFO) # Used by web page for hub info

    def do_vars(self, item):
        """vars [item]
        Show all variables, or just variables that contain item"""
        if item == "":
            pprint (variables.varList)
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
        devices.EnqueueCmd(0, ["AT+PJOIN", "OK"])

    def do_identify(self, line):
        """identify name seconds
        Sends identify command to named device.  Use 0 seconds to stop immediately"""
        argList = line.split()
        if len(argList) >= 2:
            devIdx = devices.FindDev(argList[0])
            if devIdx != None:
                timeS = int(argList[1])
                devices.Identify(devIdx, timeS)
        else:
            log.fault("Insufficient Args")

    def do_toggle(self, devId):
        """toggle name
        Sends toggle on/off command to named device"""
        devIdx = devices.FindDev(devId)
        if devIdx != None:
            devices.Toggle(devIdx)

    def do_dim(self, line):
        """dim name percentage
        Sends level command to named device"""
        argList = line.split()
        if len(argList) >= 2:
            percentage = int(argList[1])
            devIdx = devices.FindDev(argList[0])
            if devIdx != None:
                devices.Dim(devIdx, percentage)
        else:
            log.fault("Insufficient Args")

    def do_hue(self, line):
        """hue name hue
        Sends ColorCtrl command to named device, where 0<hue<360"""
        argList = line.split()
        if len(argList) >= 2:
            hue = int(argList[1])
            devIdx = devices.FindDev(argList[0])
            if devIdx != None:
                devices.Hue(devIdx, hue)
        else:
            log.fault("Insufficient Args")

    def do_sat(self, line):
        """sat name sat
        Sends ColorCtrl command to named device, where 0<sat<100"""
        argList = line.split()
        if len(argList) >= 2:
            sat = int(argList[1])
            devIdx = devices.FindDev(argList[0])
            if devIdx != None:
                devices.Sat(devIdx, sat)
        else:
            log.fault("Insufficient Args")

    def do_at(self, line):
        """at cmd
        Sends AT command to Telegesis stick"""
        devices.EnqueueCmd(0, ["AT"+line, "OK"])

