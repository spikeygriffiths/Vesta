import subprocess

result = subprocess.run(['ps', 'ax'], stdout=subprocess.PIPE)
res = result.stdout.decode().splitlines()
vesta_running = False
for item in res:
    if "vesta.py" in item:
        vesta_running = True
if vesta_running:
    print("Vesta is running")
else:
    print("Vesta stopped!")

