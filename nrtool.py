from nornir import InitNornir
from nornir.plugins.tasks.networking import netmiko_send_command
from nornir.plugins.functions.text import print_result
from nornir.core.task import Result
import argparse
import sys
from pathlib import Path
from datetime import datetime, timedelta
import yaml


# Nornir Tool
#
# -c "command" or -x command-file
# device/s or -d device-file
#
# TODO:
# -n config.yaml
# -g group -p platform --all
# -w number of workers
# autoenable if enable secret in inventory
# DEBUG = True
# SESSION_LOG = True
# AUTOENABLE = True
#
# Unfinished. A work in progess...
# working examples:
# python nrtool.py -d devices.txt -x commands.txt
# python nrtool.py cisco3 cisco4 -x commands.txt
# python nrtool.py cisco3 cisco4 -c "[{'mode': 'config', 'set': ['int lo999', 'ip address 1.1.1.1'], 'delay-factor': 4}]"
#
# More complicated, but hopefully more reliable command format
# ---
# - mode: config
#   set:
#     - int lo999
#     - ip address 10.99.9.99  255.255.255.255
# - mode: enable
#   set:
#     - wr
#     - dir
#     - show ip int bri
# - mode: interactive
#   set:
#     - copy running start
# - mode: enable
#   set:
#     - \n
#   delay_factor: 5
#
# Other supported keys
# expect_string
#


NUM_WORKERS = 1
TIMEOUT = 60

#import ipdb; ipdb.set_trace()
#OSError: Search pattern never detected in send_command_expect: cisco3\#


def netmiko_deploy(task, commands):
    net_connect = task.host.get_connection("netmiko", task.nornir.config)
    import ipdb; ipdb.set_trace()
    output = net_connect.find_prompt()
    prompt = output
    if NUM_WORKERS==1:  print(output,end='')
    result = output
    
    for group in commands:
        group_mode = group.get('mode',None)
        group_set = group.get('set', [])
        group_delay_factor = group.get('delay_factor', 1)

        if group_mode not in ('enable','config','interactive'):
            continue
        if not isinstance(group_set, list) or len(group_set)==0:
            continue
        
        if group_mode == "enable":
            for cmd_str in group_set:
                if cmd_str=='\\n':
                    cmd_str=''
                group_expect_string = group.get('expect_string', None)
                if group_expect_string:
                    output = net_connect.send_command(cmd_str,
                                                      strip_prompt=False,
                                                      strip_command=False,
                                                      delay_factor=group_delay_factor,
                                                      expect_string=rf'{group_expect_string}'
                                                      )
                else:
                    output = net_connect.send_command(cmd_str,
                                                      strip_prompt=False,
                                                      strip_command=False,
                                                      delay_factor=group_delay_factor
                                                      )                    
                if NUM_WORKERS==1:  print(output,end='')
                result += output
                
        elif group_mode == "config":
            output = net_connect.send_config_set(config_commands=group_set,
                                                 delay_factor=group_delay_factor
                                                 )
            if NUM_WORKERS==1:  print(output,end='')
            result += output
            
        elif group_mode == "interactive":
            for cmd_str in group_set:
                if cmd_str=='\\n':
                    cmd_str=''
                output = net_connect.send_command_timing(cmd_str,
                                                         strip_prompt=False,
                                                         strip_command=False,
                                                         delay_factor=group_delay_factor
                                                         )
                if NUM_WORKERS==1:  print(output,end='')
                result += output
                
        else:
            pass
        
    if NUM_WORKERS==1:  print('\n\n')
    
    return result

    
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
        commands = yaml.load(args.c)
        
    if not isinstance(args.x, type(None)):
        #check file exists
        filename = f"{args.x}"
        my_file = Path(filename)
        if not my_file.is_file():
            print(f"File {args.d} does not exist")
            sys.exit()
        #read in file
        with open(filename, "r") as f:
            commands = yaml.load(f)     

    if not isinstance(commands, list):
        print('Commands should be a list of dicts')
        sys.exit()

    #start_time = datetime.now()
    results = nr.run(task=netmiko_deploy, commands=commands)
    #elapsed_time = datetime.now() - start_time
    #print(elapsed_time)
    print_result(results)
    

        
def run():
    parser = argparse.ArgumentParser(
        description="Nornir Tool"
        ) 
    parser.add_argument(
        "-c",
        metavar="command",
        help="command array in quotes"
        )
    parser.add_argument(
        "-x",
        metavar="command file",
        help="yaml file containing list of commands"
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
