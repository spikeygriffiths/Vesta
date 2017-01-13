#!commands.py

# Command Line Interpreter module for hubapp

# Standard Python modules
import cmd
import readline
import sys
import select
# App-specific Python modules
import devices
import events
import telegesis
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

    def do_devs(self, line):
        """devs
        Show all devices"""
        print (devices.info) # ToDo: Add formatting to improve layout.  Also use cmd args to show selected bits of devices, rather than whole list
        print (devices.ephemera) # Clumsy, since it's not easy to tie each device to equivalent ephemeral index

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
        devIdx = devices.GetIdx(name)   # Try devId
        if devIdx == None:
            devIdx = devices.GetIdxFromUserName(name) # Try name if no match with devId
        if devIdx != None:
            devices.Toggle(devIdx)

    def do_dim(self, line):
        """dim name fraction
        Sends level command to named device"""
        argList = line.split()
        if len(argList) >= 2:
            devId = argList[0]
            fraction = float(argList[1])
            devIdx = devices.GetIdx(devId)   # Try devId
            if devIdx == None:
                devIdx = devices.GetIdxFromUserName(devId) # Try name if no match with devId
            if devIdx != None:
                devices.Dim(devIdx, fraction)
        else:
            log.fault("Insufficient Args")

    def do_at(self, line):
        """at cmd
        "Sends AT command to Telegesis stick"""
        telegesis.TxCmd(["AT"+line, "OK"])
        

