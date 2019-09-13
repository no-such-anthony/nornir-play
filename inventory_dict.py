from nornir import InitNornir
from collections.abc import Mapping
from pprint import pprint


#There is no single dictionary containing all inherited host information.
#This script will build one.  If you ever needed it.


def merge_dicts(dict1, dict2):
    """ 
    Recursively merges dict2 into dict1
    """
    if not isinstance(dict1, dict) or not isinstance(dict2, dict):
        return dict2
    for k in dict2:
        if k in dict1:
            dict1[k] = merge_dicts(dict1[k], dict2[k])
        else:
            dict1[k] = dict2[k]
    return dict1


def tidy_dict(d):
    """
    Remove the Nones that Nornir inserts.
    """
    if isinstance(d, Mapping):
        return {k: tidy_dict(v) for k, v in d.items() if v is not None}
    else:
        return d


def main():
    nr = InitNornir(config_file='../config.yaml')
    my_hosts = {}
    for host, host_obj in nr.inventory.hosts.items():
        my_hosts[host] = {}
        #traverse inheritance to get host connection options
        #no simple way of getting it via the host object
        host_conn_opt = tidy_dict(nr.inventory.get_inventory_dict()['defaults']['connection_options'])
        host_groups = host_obj.groups
        for group in reversed(host_groups):
            host_conn_opt = merge_dicts(host_conn_opt,
                                        tidy_dict(nr.inventory.get_inventory_dict()['groups'][group]['connection_options']))
        host_conn_opt = merge_dicts(host_conn_opt,
                                    tidy_dict(nr.inventory.get_inventory_dict()['hosts'][host]['connection_options']))       
        my_hosts[host]['connection_optons'] = host_conn_opt
        #get the remaining information from the host object
        my_hosts[host]['hostname'] = host_obj.hostname
        my_hosts[host]['platform'] = host_obj.platform
        my_hosts[host]['username'] = host_obj.username
        my_hosts[host]['password'] = host_obj.password
        my_hosts[host]['port'] = host_obj.port
        my_hosts[host]['groups'] = host_obj.groups
        my_hosts[host]['data'] = dict(host_obj.items())
    pprint(my_hosts)
    

if __name__ == "__main__":
    main()

