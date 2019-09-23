from nornir import InitNornir
from pprint import pprint


#There is no single dictionary containing all inherited host information.
#This script will build one.  If you ever needed it.


def main():
    nr = InitNornir(config_file='../config.yaml')
    my_hosts = {}
    for host, host_obj in nr.inventory.hosts.items():
        my_hosts[host] = {}
        #import ipdb; ipdb.set_trace()

        my_hosts[host]['hostname'] = host_obj.hostname
        my_hosts[host]['platform'] = host_obj.platform
        my_hosts[host]['username'] = host_obj.username
        my_hosts[host]['password'] = host_obj.password
        my_hosts[host]['port'] = host_obj.port
        my_hosts[host]['groups'] = host_obj.groups
        my_hosts[host]['data'] = dict(host_obj.items())
        #build netmiko and napalm connection parameters, show only differences from base parameters
        my_hosts[host]['connection_options'] = {}
        for conn_type in ['netmiko','napalm']:
            my_hosts[host]['connection_options'][conn_type] = {}
            if host_obj.get_connection_parameters(conn_type).hostname != host_obj.hostname:
                my_hosts[host]['connection_options'][conn_type]['hostname']=host_obj.get_connection_parameters(conn_type).hostname
            if host_obj.get_connection_parameters(conn_type).platform != host_obj.platform:
                my_hosts[host]['connection_options'][conn_type]['platform']=host_obj.get_connection_parameters(conn_type).platform
            if host_obj.get_connection_parameters(conn_type).username != host_obj.username:
                my_hosts[host]['connection_options'][conn_type]['username']=host_obj.get_connection_parameters(conn_type).username
            if host_obj.get_connection_parameters(conn_type).password != host_obj.password:
                my_hosts[host]['connection_options'][conn_type]['password']=host_obj.get_connection_parameters(conn_type).password
            if host_obj.get_connection_parameters(conn_type).port != host_obj.port:
                my_hosts[host]['connection_options'][conn_type]['port']=host_obj.get_connection_parameters(conn_type).port
            my_hosts[host]['connection_options'][conn_type]['extras']=host_obj.get_connection_parameters(conn_type).extras        
    pprint(my_hosts)
    

if __name__ == "__main__":
    main()

