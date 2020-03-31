from nornir import InitNornir
from nornir.core.filter import F
from nornir.plugins.tasks.networking import netmiko_send_command
from nornir.plugins.functions.text import print_result
import json
from pprint import pprint

EXTRAS_DIR = 'extras'


def add_extras(task,cmds=[]):
    host = task.host

    if not isinstance(cmds, list):
        return

    infile = f'{EXTRAS_DIR}/{host.name}.json'
    try:
        with open(infile) as f:
            result = json.load(f)
    except FileNotFoundError:
        result = []

    if cmds == []:
        for k in result:
            host[k] = result[k]

    else:
        for cmd in cmds:
            v = result.get(cmd,None)
            if v:
                host[cmd] = v


def get_extras(task):
    host = task.host

    ios_extras = ['show version',
                  'show cdp neighbors detail',
                  'show inventory',
                  'show interfaces switchport',
                  'show vtp status',
                  'show ip interface brief',
                  'show vlan',
                  ]

    nxos_extras = ['show version',
                  'show cdp neighbors detail',
                  'show inventory',
                  'show interfaces switchport',
                  'show ip interface brief vrf all',
                  'show vlan',
                  ]

    if host.platform=='ios':
        extras = ios_extras
    elif host.platform=='nxos':
        extras = nxos_extras
    else:
        extras = []

    my_extras={}

    for cmd in extras:
        result = task.run(task=netmiko_send_command, name=cmd, command_string=cmd, use_genie=True)
        if type(result[0].result) == str:
            result[0].result={}
            #print(f'something wrong with {host.name} on {cmd}')
        my_extras[cmd.replace(" ", "_")]=result[0].result

    o = json.dumps(my_extras)
    outfile = f'{EXTRAS_DIR}/{host.name}.json'

    with open(outfile, "w") as f:
        f.write(o)


def main():
    nr = InitNornir(config_file='../config.yaml')
    nr = nr.filter(F(platform='ios') | F(platform='nxos'))
    print(nr.inventory.hosts)
    results = nr.run(task=get_extras)
    #print_result(results)
    results = nr.run(task=add_extras,cmds=['show_version'])
    #print_result(results)
    for host, host_obj in nr.inventory.hosts.items():
        print(host, 'data')
        pprint(dict(host_obj.items()))


if __name__ == '__main__':
    main()
