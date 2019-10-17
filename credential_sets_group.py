from nornir import InitNornir
import os
import yaml
import sys

#the magic
from creds import insert_creds


def main():
    nr = InitNornir(config_file=os.path.expanduser('~/nocreds_inventory/config.yaml'),
                    logging={'enabled': False})

    print('\n\nInitial credentials')
    print('='*30)
    for host, host_obj in nr.inventory.hosts.items():
        print(f'{host}')
        print(f'Username: {host_obj.username}')
        print(f'Password: {host_obj.password}')
        print(f'Enable: {host_obj.get_connection_parameters("netmiko").extras.get("secret", None)}')
        print('-'*30)

    print('\n\nInserting credentials')
    print('='*30)
    insert_creds(nr.inventory)          
        
    print('\n\nFinal credentials')
    print('='*30)
    for host, host_obj in nr.inventory.hosts.items():
        print(f'{host}')
        print(f'Username: {host_obj.username}')
        print(f'Password: {host_obj.password}')
        print(f'Enable: {host_obj.get_connection_parameters("netmiko").extras.get("secret", None)}')
        print('-'*30)


if __name__ == '__main__':
    main()

