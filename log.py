#!log.py

from datetime import datetime
import hubapp

if __name__ == "__main__":
    hubapp.main()

def log(msg):
    timedMsg = "<" + str(datetime.now()) + ">"+ msg
    open("debug.log", "a").write(timedMsg)
    print(timedMsg)  # To stdout

def fault(msg):
    timedMsg = "<" + str(datetime.now()) + ">"+ msg
    open("fault.log", "a").write(timedMsg)
    print("FAULT! "+ msg)  # To stdout

