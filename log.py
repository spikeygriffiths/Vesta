#!log.py

import hubapp

if __name__ == "__main__":
    hubapp.main()

def log(str):
    open("debug.log", "a").write(str)
    print(str)  # To stdout

def fault(str):
    open("fault.log", "a").write(str)
    print("FAULT! "+ str)  # To stdout

