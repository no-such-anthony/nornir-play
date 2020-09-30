#!/usr/bin/env python
from nornir import InitNornir
from nornir.core.filter import F
from nornir.plugins.tasks.networking import netmiko_send_command
from nornir.plugins.functions.text import print_result
from ciscoconfparse import CiscoConfParse
import re


def checkType1(the_string, contains, avoids):
    contains_count = 0
    avoids_count = 0
    #for more exact match use'^'+contain+'$'
    #any string match in the contains array, but no string match from avoids array
    #the_string is a single string
    for contain in contains:
        if re.search(contain, the_string):
            contains_count = contains_count + 1
    for avoid in avoids:
        if re.search(avoid, the_string):
            avoids_count = avoids_count + 1
    if (avoids_count == 0) and (contains_count >= 1 or len(contains) == 0):
        return True
    return False


def checkType2(the_string, contains, avoids):
    contains_count = 0
    avoids_count = 0
    #for more exact match use '^'+contain+'$'
    #all the string matches in the contains array, but no string match from avoids array
    #remember if doing interface config there could be multiple leading spaces
    #the_string is an array of strings
    contain_store = []
    for contain in contains:
        for line in the_string:
            if re.search(contain, line):
                if contain not in contain_store:
                    #only increment once if there are multiple matches
                    contains_count = contains_count + 1
                    contain_store.append(contain)
    for avoid in avoids:
        for line in the_string:
            if re.search(avoid, line):
                avoids_count = avoids_count + 1
    if (avoids_count == 0) and (contains_count == len(contains)):
        return True
    return False


def filterByShowVersion(host, search_array=[]):
    #Filter by data found in show version

    the_show_version = host['show_version']
    the_hostname = the_show_version['hostname']
    the_hardware = the_show_version['hardware'][0]
    the_version = the_show_version['version']
    the_running_image = the_show_version['running_image']
    # etc

    #find index of search stage
    check_hostname = next((i for i, item in enumerate(search_array) if item["name"] == "hostname"), None)
    check_version = next((i for i, item in enumerate(search_array) if item["name"] == "version"), None)
    # etc

    #insert host show version data into search array
    if check_hostname is not None:
        search_array[check_hostname]['string'] = the_hostname
    if check_version is not None:
        search_array[check_version]['string'] = the_version
    #etc

    is_found = False
    for stage in search_array:
        if checkType1(the_string=stage['string'], contains=stage['contains'], avoids=stage['avoids']):
            print(f'host {host} found in stage {stage["name"]}')
            is_found = True
            continue
        else:
            print(f'host {host} not found in stage {stage["name"]}')
            is_found = False
            break

    return is_found


def filterByConfig(host, search_dict={}):
    
    the_string = host['config']
    contains = search_dict.get('contains',[])
    avoids = search_dict.get('avoids',[])

    is_found = False
    if checkType2(the_string=the_string, contains=contains, avoids=avoids):
        is_found = True
        print(f'host {host} has the config you are looking for')
    else:
        print(f'host {host} does not have the config you are looking for')

    return is_found


def filterByInterfaceConfig(host, search_dict={}):

    the_string = host['config']
    host['f_ports'] = []

    the_parent = search_dict.get('parent', None)
    contains = search_dict.get('contains',[])
    avoids = search_dict.get('avoids',[])

    is_found = False

    if not the_parent:
        return is_found
    
    #find parent and children
    parse = CiscoConfParse(the_string,factory=True)
    intf = parse.find_objects(the_parent)
    #import ipdb; ipdb.set_trace()
    for int_obj in intf:
        intf_config = []
        for obj_child in int_obj.children:
            intf_config.append(obj_child.text)
        if checkType2(the_string=intf_config,contains=contains,avoids=avoids):
            host['f_ports'].append(int_obj.text)
            print(f'host {host} and int {int_obj.text} found')
            is_found = True
            
    return is_found
            
    
def getVersion(task):
    host = task.host
    results = task.run(task=netmiko_send_command, command_string="show version",
                       use_textfsm=True)
    print(results[0].result[0])
    host['show_version'] = results[0].result[0] 

    
def getConfig(task):
    host = task.host
    results = task.run(task=netmiko_send_command, command_string="show run")
    host['config'] = results[0].result.split('\n')


def main():

    nr = InitNornir(config_file='config.yaml')
    print(nr.inventory.hosts)

    result = nr.run(task=getVersion)
    #print_result(result)

    #dynamic filter on show version results
    search_array = [
        {'name': 'hostname',
        'contains': ['R.*'],
        'avoids': ['R3']
        },
        {'name': 'version',
        'contains': ['15.2'],
        'avoids': ['15.7']
        }   
        ]
    nr = nr.filter(filter_func=filterByShowVersion, search_array=search_array)
    print(nr.inventory.hosts)

    #get config from filtered results
    result = nr.run(task=getConfig)
    #print_result(result)

    #dynamic filter on running config from the device
    search_dict = {
                'contains': ['hostname R','no ip http'],
                'avoids': ['hostname R4']
                }
    nr = nr.filter(filter_func=filterByConfig, search_dict=search_dict)
    print(nr.inventory.hosts)

    #dynamic filter on interface config from the device
    search_dict={
                'parent': 'Ethernet',
                'contains': ['ip address'],
                'avoids': ['^ duplex half']
                }
    nr = nr.filter(filter_func=filterByInterfaceConfig, search_dict=search_dict)
    print(nr.inventory.hosts)

    #print host and interface names that were found
    print('final results')
    for host, host_obj in nr.inventory.hosts.items():
        print(host, host_obj['f_ports'])

    #you can now configure just the hosts and interfaces you are interested in


if __name__ == "__main__":
    main()
