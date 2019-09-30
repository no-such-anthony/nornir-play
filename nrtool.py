from nornir import InitNornir
from nornir.plugins.tasks.networking import netmiko_send_command
from nornir.plugins.functions.text import print_result
from nornir.core.task import Result
import argparse
import sys
from pathlib import Path
from datetime import datetime, timedelta


# Nornir Tool
#
# -c "command" or -x command-file
# -n config.yaml
# device/s or -d device-file
#
# TODO:
# -g group -p platform --all
# -w number of workers
# autoenable if enable secret in inventory
# DEBUG = True
# SESSION_LOG = True
# AUTOENABLE = True
#
# Unfinished. A work in progess...
# working examples:
# python nrtool.py cisco3 cisco4 -c "sh ip int bri;sh ip arp"
# python nrtool.py cisco3 -c "conf t;int lo999;ip address 10.99.9.99 255.255.255.255;end;copy running startup;\n"
# python nrtool.py -d devices.txt -x commands.txt


NUM_WORKERS = 1
TIMEOUT = 60

#import ipdb; ipdb.set_trace()


def netmiko_deploy(task, commands):
    net_connect = task.host.get_connection("netmiko", task.nornir.config)
    output = net_connect.find_prompt()
    output_fix = False
    prompt = ''
    for cmd_str in commands:
        if cmd_str=='\\n':
            cmd_str=''
        if output_fix:
            output += '\n' + prompt
            output_fix = False
        output += net_connect.send_command_timing(cmd_str, strip_prompt=False, strip_command=False)
        start_time = datetime.now()
        while True:           
            try:
                prompt = net_connect.find_prompt()
                break
            except ValueError:
                output_fix = True
            elapsed_time = datetime.now() - start_time
            if elapsed_time > timedelta(seconds=TIMEOUT):
                raise ValueError('Timed out waiting for prompt')
    if output_fix:
        output += '\n' + prompt
    if NUM_WORKERS == 1:
        print(output)
    return output

    
def main(args):
    devices = []
    commands = []
    
    #get device list to work on
    if len(args.device)>0 and not isinstance(args.d, type(None)):
        print('Cannot have positional device arguments and the -d argument')
        sys.exit()

    if len(args.device)>0:
        devices = args.device
        
    if not isinstance(args.d, type(None)):
        #check file exists
        filename = f"{args.d}"
        my_file = Path(filename)
        if not my_file.is_file():
            print(f"File {args.d} does not exist")
            sys.exit()
        #read in file
        with open(filename, "r") as f:
            devices = f.read()
        devices = devices.split()
        
        
    if len(devices) == 0:
        print('No devices to work against')
        sys.exit()

    #filter device list
    nr = InitNornir(config_file='config.yaml',
                    core={'num_workers': NUM_WORKERS},
                    )   
    nr = nr.filter(filter_func=lambda h: h.name in args.device)
    if len(nr.inventory.hosts.keys()) == 0:
        print("No matching devices found in inventory files.")
        sys.exit()

    #get command set to run
    if not isinstance(args.c, type(None)) and not isinstance(args.x, type(None)):
        print('Cannot have command string and the -x argument')
        sys.exit()

    if not isinstance(args.c, type(None)):
        commands = args.c.split(';')
        
    if not isinstance(args.x, type(None)):
        #check file exists
        filename = f"{args.x}"
        my_file = Path(filename)
        if not my_file.is_file():
            print(f"File {args.d} does not exist")
            sys.exit()
        #read in file
        with open(filename, "r") as f:
            commands = f.read()
        commands = commands.splitlines()       
         
    if len(commands) == 0:
        print('No ommands to run')
        sys.exit()

    results = nr.run(task=netmiko_deploy, commands=commands)
    print_result(results)
    

        
def run():
    parser = argparse.ArgumentParser(
        description="Nornir Tool"
        ) 
    parser.add_argument(
        "-c",
        metavar="command",
        help="command string in quotes. separator ;"
        )
    parser.add_argument(
        "-x",
        metavar="command file",
        help="file containing list of commands"
        )
    parser.add_argument(
        "-d",
        metavar="device file",
        help="file containing list of devices"
        )
    parser.add_argument(
        'device',
        metavar='device',
        type=str,
        nargs='*',
        help='devices')
    args = parser.parse_args()
    main(args=args)


if __name__ == "__main__":
    run()
