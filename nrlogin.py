#!/usr/bin/env python
from nornir import InitNornir
import sys
import interactive
from copy import deepcopy
from pathlib import Path
import argparse
from netmiko import NetMikoAuthenticationException, NetMikoTimeoutException
import os

#Interactive shell using netmiko connection
#
#interactive.py from paramiko - https://github.com/paramiko/paramiko/blob/master/demos/interactive.py
#fix arrow/history issue with - https://github.com/rogerhil/paramiko/commit/4c7911a98acc751846e248191082f408126c7e8e
#fix pty resize and encoding  - https://github.com/sirosen/paramiko-shell/blob/master/interactive_shell.py
#
#fast_cli speeds up login times, but then you may then need to modify global delay factor for devices/platforms
#that are slow to log into, eg arista, srx...how about an optional -f [factor].

CONFIG_FILE = os.path.expanduser('~/config.yaml')
AUTOENABLE = True
FAST_CLI = True
SHELL_LOG = False
LOG_DIR = os.path.expanduser('~/session-logs')
LOG_MODE = 'w'


#Tee StdOut to File
class TeeStdOut(object):
    def __init__(self, name, mode):
        self.file = open(name, mode)
        self.stdout = sys.stdout
        sys.stdout = self

    def close(self):
        if self is None:
            return
        if self.stdout is not None:
            sys.stdout = self.stdout
            self.stdout = None
        if self.file is not None:
            self.file.close()
            self.file = None

    def write(self, data):
        self.file.write(data)
        self.stdout.write(data)

    def flush(self):
        self.file.flush()
        self.stdout.flush()

    def __del__(self):
        self.close()

        
def netmiko_interactive(task):
    host = task.host
    try:
        net_connect = task.host.get_connection("netmiko", task.nornir.config)
    except ValueError:
        print("Login process timed out looking for prompt.")
        print("Use optional argument -f <global_delay_factor>")
        print("eg -f2, and increase until login success.")
        sys.exit()
    except NetMikoAuthenticationException:
        print("Authentication failure.  Check credentials.")
        sys.exit()
    except NetMikoTimeoutException:
        print("Login timeout failure.")
        sys.exit()
        
    if AUTOENABLE:
        netmiko_extras = host.get_connection_parameters("netmiko").dict()['extras']
        #Skip if no enable secret
        if netmiko_extras.get('secret',None):
            try:
                net_connect.enable()
            except ValueError as e:
                print("Incorrect enable password.")
                
    if SHELL_LOG:
        stdout_tee = TeeStdOut(f'{LOG_DIR}/{host}.log', LOG_MODE)

    #TODO:  Print your own login banner?

    print(net_connect.find_prompt(),end='')         
    sys.stdout.flush()
    interactive.interactive_shell(net_connect.remote_conn)

    if SHELL_LOG:
        stdout_tee.close()

    
def main(args):
    #import ipdb; ipdb.set_trace()
    device_name = args.device
    gd_factor = args.f
    
    nr = InitNornir(CONFIG_FILE,
                    core={'num_workers': 1},
                    )
    nr = nr.filter(name=device_name)

    if len(nr.inventory.hosts.keys()) == 0:
        print("No matching device found in Nornir inventory.")
        sys.exit()

    if FAST_CLI or gd_factor:
        for host, host_obj in nr.inventory.hosts.items():
            netmiko_params = host_obj.get_connection_parameters("netmiko")
            extras = deepcopy(netmiko_params.extras)
            if FAST_CLI:  extras["fast_cli"] = True
            if gd_factor:  extras["global_delay_factor"] = gd_factor
            netmiko_params.extras = extras
            host_obj.connection_options["netmiko"] = netmiko_params

    if SHELL_LOG:
        Path(f"{LOG_DIR}").mkdir(exist_ok=True)
            
    nr.run(task=netmiko_interactive)


if __name__ == "__main__":
    
    parser = argparse.ArgumentParser(
        description="Nornir Login"
        ) 
    parser.add_argument(
        "-f",
        metavar="factor",
        type=int,
        help="global delay factor - for devices with slow logins"
        )
    parser.add_argument(
        'device',
        metavar='device',
        type=str,
        help='device name from Nornir inventory to connect to')
    args = parser.parse_args()
    main(args=args)
    
