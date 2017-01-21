#!commands.py

# Command Line Interpreter module for hubapp

# Standard Python modules
import cmd
import readline
import sys
import select
from pathlib import Path
from pprint import pprint # Pretty print for devs list
# App-specific Python modules
import devices
import events
import telegesis
import variables
import rules
import hubapp

if __name__ == "__main__":
    hubapp.main()

def EventHandler(eventId, eventArg):
    if eventId == events.ids.SECONDS:
        if select.select([sys.stdin], [], [], 0)[0]:
            cmd = sys.stdin.readline()
            if cmd:
                Commands().onecmd(cmd)
    # End of Command EventHandler

class Commands(cmd.Cmd):
    
    def do_info(self, line):
        """info
        Displays useful information"""
        events.Issue(events.ids.INFO)

    def do_devs(self, term):
        """devs [<term>]
        Show all devices, or just fragments that contain <term>"""
        if term == "":
            pprint (devices.info)
            pprint (devices.ephemera) # Clumsy, since it's not easy to tie each device to equivalent ephemeral index
        else:
            itemisedList = []
            for device in devices.info:
                for item in device:
                    if term.lower() in item[0].lower():
                        itemisedList.append(item)
            for device in devices.ephemera:
                for item in device:
                    if term.lower() in item[0].lower():
                        itemisedList.append(item)
            pprint (itemisedList)

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

    def do_rules(self, item):
        """rules [item]
        Show all rules, or just rules that contain [item]"""
        filename = rules.rulesFilename
        rulesFile = Path(filename)
        if rulesFile.is_file():
            with open(filename) as rulesTxt:
                for line in rulesTxt:
                    if item != None and item.lower() in line.lower():
                        print(line, end="")

    def do_open(self, line):
        """open
        Opens network (for 60s) to allow new device to join"""
        telegesis.TxCmd(["AT+PJOIN", "OK"])

    def do_new(self, devId):
        """new devId
        Add new device with devId of 4 hex digits to device list"""
        if devId != None:
            devices.InitDev(devId)

    def do_name(self, line):
        """name devId name
        Allows user to associate friendly name with device Id"""
        argList = line.split()
        devId = argList[0]
        name = argList[1]
        if devId != None and name != None:
            devIdx = devices.GetIdx(devId)
            if devIdx != None:
                devices.SetVal(devIdx, "UserName", name)
        else:
            log.fault("Need both args!")

    def do_toggle(self, name):
        """toggle name
        Sends toggle on/off command to named device"""
        devIdx = devices.GetIdxFromUserName(name) # Try name first
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
        

