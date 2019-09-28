from nornir import InitNornir
import sys
import interactive

#Interactive shell using netmiko connection
#interactive.py found in paramiko demo directory
#fix arrow/history issue with - https://github.com/rogerhil/paramiko/commit/4c7911a98acc751846e248191082f408126c7e8e
#fast_cli speeds up login times

def netmiko_interactive(task):
    net_connect = task.host.get_connection("netmiko", task.nornir.config)
    print(net_connect.find_prompt(),end='')
    sys.stdout.flush()
    interactive.interactive_shell(net_connect.remote_conn)
    
if len(sys.argv) == 2:
    hostname = sys.argv[1]
else:
    print("Hostname required.")
    sys.exit(1)

nr = InitNornir('config.yaml')
nr = nr.filter(name=hostname)

results = nr.run(task=netmiko_interactive)
