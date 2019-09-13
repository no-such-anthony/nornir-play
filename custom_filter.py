from nornir import InitNornir
from nornir.core.filter import F
from nornir.plugins.tasks.networking import netmiko_send_command
from nornir.plugins.functions.text import print_result
from ciscoconfparse import CiscoConfParse
import re


'''
in defaults.yaml

data:
  my_show_version: dummy
  my_config: dummy
  f_ports: dummy
'''

def checkType1(my_string, contains, avoids):
    contains_count = 0
    avoids_count = 0
    #for more exact match use'^'+contain+'$'
    #any string match in the contains array, but no string match from avoids array
    #my_string is a single string
    for contain in contains:
        if re.search(contain, my_string):
            contains_count = contains_count + 1
    for avoid in avoids:
        if re.search(avoid, my_string):
            avoids_count = avoids_count + 1
    if (avoids_count == 0) and (contains_count >= 1 or len(contains) == 0):
        return True
    return False

def checkType2(my_string, contains, avoids):
    contains_count = 0
    avoids_count = 0
    #for more exact match use '^'+contain+'$'
    #all the string matches in the contains array, but no string match from avoids array
    #remember if doing interface config there could be multiple leading spaces
    #my_string is an array of strings
    contain_store = []
    for contain in contains:
        for line in my_string:
            if re.search(contain, line):
                if contain not in contain_store:
                    #only increment once if there are multiple matches
                    contains_count = contains_count + 1
                    contain_store.append(contain)
    for avoid in avoids:
        for line in my_string:
            if re.search(avoid, line):
                avoids_count = avoids_count + 1
    if (avoids_count == 0) and (contains_count == len(contains)):
        return True
    return False
                
def filterByShowVersion(host):

    my_show_version = host['my_show_version']
    my_hostname = my_show_version['hostname']
    my_hardware = my_show_version['hardware'][0]
    my_version = my_show_version['version']
    my_running_image = my_show_version['running_image']
    # etc

    filter_array = [
        {'name': 'hostname',
         'string': my_hostname,
         'contains': ['c.*'],
         'avoids': []
        },
        {'name': 'version',
         'string': my_version,
         'contains': [],
         'avoids': ['16.7']
        }   
        ]

    is_found = False
    for stage in filter_array:
        if checkType1(my_string=stage['string'], contains=stage['contains'], avoids=stage['avoids']):
            print(f'host {host} found in stage {stage["name"]}')
            is_found = True
            continue
        else:
            print(f'host {host} not found in stage {stage["name"]}')
            is_found = False
            break

    return is_found

def filterByConfig(host):
    
    my_string = host['my_config']
    contains = ['hostname cisco3','no ip http']
    avoids = []
    
    is_found = False
    if checkType2(my_string=my_string, contains=contains, avoids=avoids):
        is_found = True
        print(f'host {host} has the config you are looking for')
        
    return is_found

def filterByInterfaceConfig(host):

    my_string = host['my_config']
    host['f_ports'] = []

    my_parent = 'Ethernet'
    contains = ['ip address']
    avoids = ['^ shut']
    
    is_found = False
    
    #find parent and children
    parse = CiscoConfParse(my_string,factory=True)
    intf = parse.find_objects(my_parent)
    #import ipdb; ipdb.set_trace()
    for int_obj in intf:
        intf_config = []
        for obj_child in int_obj.children:
            intf_config.append(obj_child.text)
        if checkType2(my_string=intf_config,contains=contains,avoids=avoids):
            host['f_ports'].append(int_obj.text)
            print(f'host {host} and int {int_obj.text} found')
            is_found = True
            
    return is_found
            
    
def getVersion(task):
    host = task.host
    results = task.run(task=netmiko_send_command, command_string="show version",
                       use_textfsm=True)
    print(results[0].result[0])
    host['my_show_version'] = results[0].result[0] 

    
def getConfig(task):
    host = task.host
    results = task.run(task=netmiko_send_command, command_string="show run")
    host['my_config'] = results[0].result.split('\n')

    
nr = InitNornir(config_file='config.yaml')
filt = F(groups__contains="ios")
nr = nr.filter(filt)

print(nr.inventory.hosts)

result = nr.run(task=getVersion)
print_result(result)

#dynamic filter on show version results
nr = nr.filter(filter_func=filterByShowVersion)
print(nr.inventory.hosts)

#get config from filtered results
result = nr.run(task=getConfig)
print_result(result)

#dynamic filter on config on the device
nr = nr.filter(filter_func=filterByConfig)
print(nr.inventory.hosts)

#dynamic filter on interface config on the device
nr = nr.filter(filter_func=filterByInterfaceConfig)
print(nr.inventory.hosts)

#print host and interfaces names that were found
print('final results')
for host, host_obj in nr.inventory.hosts.items():
    print(host, host_obj['f_ports'])


