import subprocess
import database
import sendmail
import time

def check(app_name):
    result = subprocess.run(['ps', 'ax'], stdout=subprocess.PIPE)
    res = result.stdout.decode().splitlines()
    app_running = False
    for item in res:
        if app_name in item:
            app_running = True
    if not app_running:
        database.ConnectDb()
        result = subprocess.run(['tail', 'logs/today.log', "-n", "20"], stdout=subprocess.PIPE)
        text = result.stdout.decode().splitlines()
        sendmail.email(app_name + " stopped", text, "")
        subprocess.run(["sudo", "/bin/vesta.sh"]) # Restart app

while True:
    check("vesta.py")
    time.sleep(60)
