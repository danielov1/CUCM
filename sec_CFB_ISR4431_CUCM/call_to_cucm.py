################ This code configure Secure Conference Bridge (CUCM Side)###################

import paramiko
import time
import os
import configparser

time.sleep(1)
# CUCM connection details
config = configparser.ConfigParser()
config.read('connection.ini')

ip = config['cucm']['ip']
username = config['cucm']['username']
password = config['cucm']['password']
router = config['routers']['ip']
domain = config['cucm']['domain']
cucmHostName = config['cucm']['hostname']

print('My configuration:')
print(f'CUCM IP: {ip}')
print(f'User: {username}')


host = ip

# Connect to CUCM via SSH
remote_conn_pre = paramiko.SSHClient()
remote_conn_pre
remote_conn_pre.set_missing_host_key_policy(paramiko.AutoAddPolicy())
remote_conn_pre.connect(ip, username=username, password=password, look_for_keys=False, allow_agent=False, timeout=60)
print("SSH connection established to " + host)
remote_conn = remote_conn_pre.invoke_shell()
print("Interactive SSH session established")
time.sleep(15)


# Upload CFB Router certificate to CUCM server
with open(router + '.txt', 'r') as myfile:
  data = myfile.read()
remote_conn.send("\n")
remote_conn.send("set cert import trust CallManager\r")
time.sleep(15)
remote_conn.send((data))#send VGW CFB cert to CUCM
time.sleep(15)
output = remote_conn.recv(50000)

print(output)
