from nornir import InitNornir
import os
import yaml

from ansible.parsing.vault import VaultLib, VaultSecret
from ansible.cli import CLI
from ansible.parsing.dataloader import DataLoader


def decrypt_vault(
    filename, vault_password=None, vault_password_file=None, vault_prompt=False
):
    """
    filename: name of your encrypted file that needs decrypted.
    vault_password: key that will decrypt the vault.
    vault_password_file: file containing key that will decrypt the vault.
    vault_prompt: Force vault to prompt for a password if everything else fails.
    """

    loader = DataLoader()
    if vault_password:
        vault_secret = [([], VaultSecret(vault_password.encode()))]
    elif vault_password_file:
        vault_secret = CLI.setup_vault_secrets(
            loader=loader, vault_ids=[vault_password_file]
        )   
    else:
        vault_secret = CLI.setup_vault_secrets(
            loader=loader, vault_ids=[], auto_prompt=vault_prompt
        )   

    vault = VaultLib(vault_secret)

    with open(filename) as f:
        unencrypted_yaml = vault.decrypt(f.read())
        unencrypted_yaml = yaml.safe_load(unencrypted_yaml)
        return unencrypted_yaml


#list in a standalone yaml file, or defaults.yaml
#have a prefix in set/group name? eg creds_ios, etc
#a device should only have a single credential set/group
credential_sets = ['ios','nxos','eos','junos']

#credentials.yaml encrypted with vault
#
#---
#ios:
#  username: fred
#  password: flintstone
#nxos:
#  username: barney
#  password: rubble
#eos:
#  username: bambam
#  password: rubble
#junos:
#  username: neo
#  password: spoonboy

#removed username and password from defaults.yaml

#move class and transform into their own python file so other scripts can import?
class credentialStore:
    def __init__(self):
        self.creds = self._get_creds()


    def _get_creds(self):
        filename = os.path.expanduser('~/nocreds_inventory/credentials.yaml')
        password_file = os.path.expanduser('~/nocreds_inventory/shallnotpass.txt')
        result = decrypt_vault(filename=filename,vault_password_file=password_file)        
        return dict(result)

        
    def get(self, group):
        #what about enable and other connection parameters?
        username = None
        password = None
        if group in self.creds:
            username = self.creds[group].get('username', None)
            password = self.creds[group].get('password', None)          
        return username, password


def credential_transform(host, creds): 
    #only check credential sets if none already present
    if not host.username or not host.password:
        for group in host.groups:
            username = None
            password = None
            if group in credential_sets:
                username, password = creds.get(group)
                #only one credential set per device
                break
        if not host.username:
            host.username = username
        if not host.password:
            host.password = password

                
def main():
    creds = credentialStore()
    transform_options = { 'creds': creds }
    nr = InitNornir(config_file=os.path.expanduser('~/nocreds_inventory/config.yaml'),
                    logging={'enabled': False},
                    inventory={'transform_function':
                               'credential_sets_transform.credential_transform',
                               'transform_function_options': transform_options})
       
    print('\n\nFinal credentials')
    print('='*30)
    for host, host_obj in nr.inventory.hosts.items():
        print(f'{host}')
        print(f'Username: {host_obj.username}')
        print(f'Password: {host_obj.password}')
        print('-'*30)


if __name__ == '__main__':
    main()

