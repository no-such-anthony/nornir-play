from nornir import InitNornir
import sys
import interactive
from copy import deepcopy
from pathlib import Path

#Interactive shell using netmiko connection
#interactive.py found in paramiko demo directory
#fix arrow/history issue with - https://github.com/rogerhil/paramiko/commit/4c7911a98acc751846e248191082f408126c7e8e
#fast_cli speeds up login times

AUTOENABLE = True
FAST_CLI = True


def netmiko_interactive(task):
    host = task.host
    net_connect = task.host.get_connection("netmiko", task.nornir.config)
    #TODO:  Print your own login banner?
    if AUTOENABLE:
        netmiko_extras = host.get_connection_parameters("netmiko").dict()['extras']
        #Skip if no enable secret
        if netmiko_extras.get('secret',None):
            try:
                net_connect.enable()
            except ValueError as e:
                print("Incorrect enable password.")
    print(net_connect.find_prompt(),end='')
    sys.stdout.flush()
    interactive.interactive_shell(net_connect.remote_conn)

    
def main(device_name):
    nr = InitNornir('config.yaml',
                    core={'num_workers': 1},
                    )
    nr = nr.filter(name=device_name)

    if FAST_CLI:
        for host, host_obj in nr.inventory.hosts.items():
            netmiko_params = host_obj.get_connection_parameters("netmiko")
            extras = deepcopy(netmiko_params.extras)
            extras["fast_cli"] = True
            netmiko_params.extras = extras
            host_obj.connection_options["netmiko"] = netmiko_params
            
    nr.run(task=netmiko_interactive)


if __name__ == "__main__":
    if len(sys.argv) == 2:
        device_name = sys.argv[1]
    else:
        print("Device name required.")
        sys.exit(1)
    main(device_name=device_name)
