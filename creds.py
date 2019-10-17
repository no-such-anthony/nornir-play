from ansible.parsing.vault import VaultLib, VaultSecret
from ansible.cli import CLI
from ansible.parsing.dataloader import DataLoader
from copy import deepcopy
import os
import yaml

#see credential_sets_group.py for it in use

#credentials.yaml encrypted with vault
#
#---
#ios:
#  username: fred
#  password: flintstone
#  enable: leroy
#nxos:
#  username: barney
#  password: rubble
#eos:
#  username: bambam
#  password: rubble
#junos:
#  username: neo
#  password: spoonboy


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


class credentialStore:
    def __init__(self):
        self.creds = self._creds()

    def _creds(self):
        filename = os.path.expanduser('~/nocreds_inventory/credentials.yaml')
        password_file = os.path.expanduser('~/nocreds_inventory/shallnotpass.txt')
        result = decrypt_vault(filename=filename,vault_password_file=password_file)        
        return dict(result)
        
    def base(self, group):
        username = None
        password = None
        enable = None
        if group in self.creds:
            username = self.creds[group].get('username', None)
            password = self.creds[group].get('password', None)
            enable = self.creds[group].get('enable', None)
        return (username, password, enable)

    def groups(self):
        return list(self.creds.keys())


def insert_creds(inventory=object):
    creds = credentialStore()
    credential_sets = creds.groups()
    for group, group_obj in inventory.groups.items():
        if group in credential_sets:
            username, password, enable = creds.base(group)
            group_obj.username = username
            group_obj.password = password
            if enable:
                netmiko_params = group_obj.get_connection_parameters("netmiko")
                extras = deepcopy(netmiko_params.extras)
                extras["secret"] = enable
                netmiko_params.extras = extras
                group_obj.connection_options["netmiko"] = netmiko_params
