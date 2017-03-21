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
# App-specific Python modules
import devices
import events
import telegesis
import variables
import rules
import hubapp
import log

sck = ""
cliSck = ""
sckLst = []

if __name__ == "__main__":
    hubapp.main()

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
                log.log ("New connection from web page!")
            else:
                cmd = cliSck.recv(100)
                if cmd:
                    cmd = cmd.decode()
                    log.log ("Got cmd "+ cmd)
                    Commands().onecmd(cmd)
                    #cliSck.send(str.encode("Hello from Python!"))
                else:
                    log.log ("Closing socket")
                    cliSck.close()
                    sckLst.remove(cliSck)
    # End of Command EventHandler

class Commands(cmd.Cmd):
    
    def do_info(self, line):
        """info
        Displays useful information"""
        events.Issue(events.ids.INFO)

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
        telegesis.TxCmd(["AT+PJOIN", "OK"])

    def do_toggle(self, name):
        """toggle name
        Sends toggle on/off command to named device"""
        devIdx = database.GetDevIdx("userName", name) # Try name first
        if devIdx == None:
            devIdx = devices.GetIdx(name)   # Try devId if no name match
        if devIdx != None:
            devices.Toggle(devIdx)

    def do_dim(self, line):
        """dim name fraction
        Sends level command to named device"""
        argList = line.split()
        if len(argList) >= 2:
            devId = argList[0]
            fraction = float(argList[1])
            devIdx = devices.GetIdxFromUserName(name) # Try name first
            if devIdx == None:
                devIdx = devices.GetIdx(name)   # Try devId if no name match
            if devIdx != None:
                devices.Dim(devIdx, fraction)
        else:
            log.fault("Insufficient Args")

    def do_at(self, line):
        """at cmd
        "Sends AT command to Telegesis stick"""
        telegesis.TxCmd(["AT"+line, "OK"])
        

