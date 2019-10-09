from nornir import InitNornir
from nornir.core.filter import F
from nornir.plugins.functions.text import print_result
from nornir.plugins.tasks.files import write_file
from nornir.plugins.tasks.networking import netmiko_send_command
from datetime import datetime
import re

BACKUPDIR = 'configs'
DIFFDIR = 'diffs'

def backup(task, path):
  host = task.host
  data = task.run(task=netmiko_send_command,
                 command_string='show running-config',
                 enable=True)

  regex1 = re.compile('^ntp clock-period.*$', re.MULTILINE)
  regex2 = re.compile('^!Time.*$',re.MULTILINE)
  data.result = regex1.sub('', data.result)
  data.result = regex2.sub('', data.result)

  task.run(write_file,
           filename=f'{path}/{host}.cfg',
           content=data.result)
 
def main():
  nr = InitNornir(config_file='../config.yaml',
                  core={'num_workers': 15},
                  )
  ios_filt = ~F(platform="cisco_wlc") #& F(name='xxxxx')
  ios = nr.filter(ios_filt)
  start_time = datetime.now()
  result = ios.run(task=backup, path=BACKUPDIR)
  elapsed_time = datetime.now() - start_time

  print('-'*50)
  print("Results")
  print('-'*50)
  for host, multiresult in result.items():
    print(host,end='')
    if multiresult.failed:
        print(' - failed, check nornir.log')
        continue
    for r in multiresult:
      if r.name == 'write_file':
        if not r.changed:
          print(' - no change in config stored')
        else:
          print(' - differences found in config stored')
          diff_time = datetime.now()
          filename = f'{DIFFDIR}/{host}--{diff_time.strftime("%d-%m-%y-%X")}.txt'
          with open(filename, 'w') as f:
            f.write(r.diff)
  print('-'*50)
  print("Elapsed time: {}".format(elapsed_time))

if __name__ == "__main__":
  main()


#Issues.  With 20 workers on 1300 devices I experienced the following random errors (low rate)
#1.netmiko.ssh_exception.NetMikoTimeoutException: Timed-out reading channel, data not available.
#2.ValueError: Failed to enter enable mode. Please ensure you pass the 'secret' argument to ConnectHandler
#3.Corrupt backups < 100 characters
#
#Fixes
#- use netmiko 3.0 develop branch
#- use blocking_timeout: 20 in extras (possible TACACS+ throttling)
#and/or 
#- keep reducing num_workers
#
#
#Diff Issues
#A lot of Cisco devices will show these in the diffs...hence the pre-processing before write_file
#
#-!Time: Wed Oct  9 11:02:39 2019
#+!Time: Wed Oct  9 14:53:31 2019
#and
#-ntp clock-period 36028974
#+ntp clock-period 36028975
#
#
