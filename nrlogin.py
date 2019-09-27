import subprocess
import sys
from nornir import InitNornir

#Interactive ssh after automatic login with nornir credentials

if len(sys.argv) == 2:
    hostname = sys.argv[1]
else:
    print("Hostname required.")
    sys.exit(1)

nr = InitNornir('config.yaml')
host = nr.inventory.hosts[hostname]

hostname = host.hostname
username = host.username
password = host.password

status = subprocess.call("sshpass" + f" -p {password} ssh -l {username} {hostname}", shell=True)
