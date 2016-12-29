#!log.py

import hubapp

if __name__ == "__main__":
    hubapp.main()

def log(str):
    with open("hubapp.log", "a") as f:
        f.write(str)
        print(str)  # To stdout
