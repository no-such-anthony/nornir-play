from nornir import InitNornir
from nornir.plugins.tasks.networking import netmiko_send_command
from nornir.plugins.functions.text import print_result
from copy import deepcopy
import logging


TRANSFORM_FUNCTION = 'extra_logging.transform_slog2'
#TRANSFORM_FUNCTION = ''

#access to logger
logger = logging.getLogger("nornir")


def transform_slog2(host):
    """
    This pattern retrieves the entire set of connection parameters recursively.
    It then makes an update to extras.
    Finally, it re-assigns this updated set of connection parameters back at the
    host level.
    By Kirk!
    """

    # Dynamically set the session_log to be unique per host
    filename = f"{host}-output.txt"

    # Retrieve the current set of connection parameters recursively
    netmiko_params = host.get_connection_parameters("netmiko")

    # Dictionaries are mutable so we can run into issues with the dictionary
    # being shared across hosts (i.e. we grab the dict from the group-level
    # and then keep using it). Make a copy instead.
    extras = deepcopy(netmiko_params.extras)
    extras["session_log"] = filename
    extras["session_log_file_mode"] = "append"
    netmiko_params.extras = extras

    # Re-assign the entire set of connection options back at the host-level
    host.connection_options["netmiko"] = netmiko_params

    
def my_task(task):
  logger.info(f"Executing commands on {task.host}")
  result0 = task.run(task=netmiko_send_command, name="show clock", command_string='show clock', use_textfsm=True)
  result1 = task.run(task=netmiko_send_command, name="show interface status", command_string='show interface status', use_textfsm=True)
  result2 = task.run(task=netmiko_send_command, name="show version", command_string='show version', use_textfsm=True)

def main():
  
  nr = InitNornir(config_file='config.yaml',
                  inventory={'transform_function': TRANSFORM_FUNCTION},
                  logging={'enabled': True}
                  )
  nr = nr.filter(platform='ios')
  
  agg_result = nr.run(task=my_task, name="My Task")
  print_result(agg_result)

if __name__ == "__main__":
  main()

