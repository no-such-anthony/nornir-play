from nornir import InitNornir
from nornir.plugins.tasks.networking import netmiko_send_command
from nornir.plugins.functions.text import print_result
from nornir.core.task import Result
import argparse
import sys

#
#wlan id is found via the gui or cli - show wlan summary
#requires <ssid>: <wlan_id> data variable
#example hosts.yaml
#---
#my-wlc01:
#  hostname: my-wlc01
#  username: 
#  password: 
#  platform: wlc
#  connection_options:
#    netmiko:
#      platform: cisco_wlc
#  data:
#    events: 4
#

def change_psk(task, new_psk, ssid):
  changed = False

  wlan_id = task.host.get(ssid, None)
  if wlan_id is None:
    return Result(host=task.host, changed=changed, failed=True, result=f"Could not find {ssid} in data variables.")

  if not isinstance(wlan_id, int):
    return Result(host=task.host, changed=changed, failed=True, result=f"The wlan_id for {ssid} needs to be an integer.")

  cmd_array = [f'config wlan disable {wlan_id}',
               f'config wlan security wpa akm psk set-key ascii {new_psk} {wlan_id}',
               f'config wlan enable {wlan_id}',
              ]
  
  #cmd_array_testing = [f'config wlan disable {wlan_id}',
  #             f'config wlan enable {wlan_id}',
  #            ]

  for cmd_str in cmd_array:
    r = task.run(task=netmiko_send_command, name=cmd_str, command_string=cmd_str)
    if len(r.result.strip()) != 0:
      #Likely an error.  Successful commands have no output.
      return Result(host=task.host, changed=changed, failed=True, result='An error occurred during task.')

  changed = True
  
  #save config
  r = task.run(task=netmiko_send_command, name="save config", command_string="save config", use_timing=True, strip_prompt=False, strip_command=False)
  if "Are you sure" in r.result:
    r = task.run(task=netmiko_send_command, name="save (y/n)", command_string="y", use_timing=True, strip_prompt=False, strip_command=False)

  return Result(host=task.host, changed=changed, failed=False, result='Changed PSK.')

def main(new_psk, ssid, device):

  #print("Arguments:", new_psk, ssid, device)

  nr = InitNornir(config_file='config.yaml')
  nr = nr.filter(platform='wlc')
  #print(nr.inventory.hosts)

  if device:
    nr = nr.filter(filter_func=lambda h: h.name in device)
    print('Optionally filtered to hosts:')
    print(nr.inventory.hosts)
  results = nr.run(task=change_psk, new_psk=new_psk, ssid=ssid)
  print_result(results)


def run():
  parser = argparse.ArgumentParser(
    description="Tool to change PSK for SSID on Cisco WLCs"
  ) 
  parser.add_argument(
    "-p","--psk",
    required=True,
    metavar="<psk>",
    help="New PSK for SSID. Required."
  )
  parser.add_argument(
    "-s","--ssid",
    required=True,
    metavar="<ssid>",
    help="What SSID to change the PSK for.  Required."
  )
  parser.add_argument(
    "-d","--device",
    action='append',
    metavar="<wlc>",
    help="Filter to this WLC.  Pass this option again to add as many WLCs you want to filter to. Optional"
  )
  args = parser.parse_args()

  if len(args.psk) < 8:
    print("The new psk needs to be a minimum of 8 characters.")
    sys.exit(1)
  
  main(args.psk, args.ssid, args.device)


if __name__ == "__main__":
  run()


#Known WLC error output:
#Request failed for WLAN 6 - WLAN Identifier is invalid.
#Incorrect input! Use 'config wlan security wpa akm [802.1x/psk/cckm/ft/ft psk/pmf 801.x/pmf psk] [enable/disable] <wlan ID>
#Do I care if flash is busy and it isn't saved?
#if "Configuration Saved" not in r.result:
