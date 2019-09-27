#!/usr/bin/env python

#Proof of concept only, interactive ssh after automatic login with nornir credentials
#
#slightly modified paramiko demo.py using nornir for hostname,username,password
#Requires paramiko interactive.py
#


import os
import socket
import sys
import time
import traceback
from paramiko.py3compat import input
import paramiko
import interactive
from nornir import InitNornir


def agent_auth(transport, username):
    """
    Attempt to authenticate to the given transport using any of the private
    keys available from an SSH agent.
    """

    agent = paramiko.Agent()
    agent_keys = agent.get_keys()
    if len(agent_keys) == 0:
        return

    for key in agent_keys:
        print("Trying ssh-agent key %s" % hexlify(key.get_fingerprint()))
        try:
            transport.auth_publickey(username, key)
            print("... success!")
            return
        except paramiko.SSHException:
            print("... nope.")


if len(sys.argv) == 2:
    hostname = sys.argv[1]
else:
    print("*** Hostname required.")
    sys.exit(1)

    
nr = InitNornir('config.yaml')
host = nr.inventory.hosts[hostname]

port = 22
hostname = host.hostname
username = host.username
password = host.password
    

# now connect
try:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((hostname, port))
except Exception as e:
    print("*** Connect failed: " + str(e))
    traceback.print_exc()
    sys.exit(1)

try:
    keys = paramiko.util.load_host_keys(
        os.path.expanduser("~/.ssh/known_hosts")
    )
except IOError:
    try:
        keys = paramiko.util.load_host_keys(
            os.path.expanduser("~/ssh/known_hosts")
        )
    except IOError:
        print("*** Unable to open host keys file")
        keys = {}
            
try:
    t = paramiko.Transport(sock)
    try:
        t.start_client()
    except paramiko.SSHException:
        print("*** SSH negotiation failed.")
        sys.exit(1)

    # check server's host key -- this is important.
    key = t.get_remote_server_key()
    if hostname not in keys:
        print("*** WARNING: Unknown host key!")
    elif key.get_name() not in keys[hostname]:
        print("*** WARNING: Unknown host key!")
    elif keys[hostname][key.get_name()] != key:
        print("*** WARNING: Host key has changed!!!")
        sys.exit(1)
    else:
        print("*** Host key OK.")

    agent_auth(t, username)
    t.auth_password(username, password)

    if not t.is_authenticated():
        print("*** Authentication failed. :(")
        t.close()
        sys.exit(1)

    chan = t.open_session()
    chan.get_pty()
    chan.invoke_shell()
    print("*** Here we go!\n")
    interactive.interactive_shell(chan)
    chan.close()
    t.close()

except Exception as e:
    print("*** Caught exception: " + str(e.__class__) + ": " + str(e))
    traceback.print_exc()
    try:
        t.close()
    except:
        pass
    sys.exit(1)
    

