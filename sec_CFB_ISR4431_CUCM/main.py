################# This code configure Secure Conference Bridge (Router Side)##################
import paramiko
import time
import os
import configparser

# config file information
config = configparser.ConfigParser()
config.read('connection.ini')

# config file parameters
ip = config['routers']['ip']
username = config['routers']['username']
password = config['routers']['password']
domain = config['cucm']['domain']
cucmHostName = config['cucm']['hostname']
routerHostName = config['routers']['hostname']
cucmIP = config['cucm']['ip']
voicecard = config['routers']['voicecard']
gigInterface = config['routers']['gigInterface']
cmCertPath = config['cucm']['cmCertPath']

print('My configuration:')
print(f'Router IP: {ip}')
print(f'User: {username}')
print(f'Domain: {domain}')


host = ip
router = ip


time.sleep(1)
# Connect to Router via SSH
remote_conn_pre = paramiko.SSHClient()
remote_conn_pre
remote_conn_pre.set_missing_host_key_policy(paramiko.AutoAddPolicy())
remote_conn_pre.connect(ip, username=username, password=password, look_for_keys=False, allow_agent=False, timeout=60)
print("SSH connection established to " + host)
remote_conn = remote_conn_pre.invoke_shell()
print("Interactive SSH session established")

output = remote_conn.recv(1000)
print(output)   

# Configure initial configuration and reload the route
remote_conn.send("\n")
remote_conn.send("conf t\n")
remote_conn.send("hostname " + routerHostName + "\n")
remote_conn.send("\n")
remote_conn.send("show ver | i securityk9\n")
time.sleep(5)
output = remote_conn.recv(5000)
chains = output.split()
if "None" in str(output): # Check if Securityk9 license installed
    remote_conn.send("conf t\n")
    remote_conn.send("license boot level securityk9\n")
    remote_conn.send("yes\n")
    remote_conn.send("exit\n")
    remote_conn.send("wr\n")
    remote_conn.send("reload\n")
    remote_conn.send("yes\n")
    remote_conn.send("\r")
    remote_conn.send("\r")
    remote_conn.send("\r")
    time.sleep(60)
i=0
response = os.system('cmd /c "ping" ' "" + ip)
while response == 1:
    i = i+1
    if(i>9):
        break
    time.sleep(60)
    response = os.system('cmd /c "ping" ' "" + ip)

time.sleep(1)
# Configure CFB Router
remote_conn.send("conf t\n")
remote_conn.send("crypto key Generate rsa general-keys label CFBROUTER modulus 1024\n")
remote_conn.send("crypto pki trustpoint CFBROUTER\n")
remote_conn.send("enrollment selfsigned\n")
remote_conn.send("rsakeypair CFBROUTER\n")
remote_conn.send("fqdn none\n")
remote_conn.send("revocation-check none\n")
remote_conn.send("subject-name CN=CFBROUTER\n")
remote_conn.send("crypto pki enroll CFBROUTER\n")
#remote_conn.send("yes\n") # Some routers needs to answer yes
remote_conn.send("no\n")
remote_conn.send("no\n")
remote_conn.send("yes\n")
remote_conn.send("exit\n")
time.sleep(5)

output = remote_conn.recv(5000)
print(output)

# Open file to create Router certificate
file = open(router + '.txt', 'wb')

# Copy file to file above
remote_conn.send("conf t\n")
remote_conn.send("crypto pki export CFBROUTER pem terminal\n")
time.sleep(5)
output = remote_conn.recv(5000)
startCertCFB = output.index(('-----BEGIN CERTIFICATE-----').encode())
endCertCFB = output.index(('% General').encode())
fullCertCFB = output[startCertCFB:endCertCFB]
print(fullCertCFB)
file.write(fullCertCFB)
file.close()

# Call to CFB_CUCM code
import call_to_cucm

# Connect again to Router via SSH
remote_conn_pre = paramiko.SSHClient()
remote_conn_pre
remote_conn_pre.set_missing_host_key_policy(paramiko.AutoAddPolicy())
remote_conn_pre.connect(ip, username=username, password=password, look_for_keys=False, allow_agent=False)
print("SSH connection established to " + host)  
remote_conn = remote_conn_pre.invoke_shell()
print("Interactive SSH session established")

output = remote_conn.recv(1000)
print(output)   

with open(cmCertPath , 'r') as myfile:
  data = myfile.read()

# Configure CUCM Trust Point
remote_conn.send("\n")
remote_conn.send("conf t\n")
remote_conn.send("crypto pki trustpoint" + " " + cucmHostName + domain + "\n")
remote_conn.send("enrollment terminal\n")
remote_conn.send("subject-name CN=" + cucmHostName + domain + "\n")
remote_conn.send("revocation-check none\n")
remote_conn.send("exit\n")
remote_conn.send("crypto ca authenticate" + " " + cucmHostName + domain + "\r")
remote_conn.send((data + "\r"))#send CUCM cert to CFB
remote_conn.send("yes\n")
remote_conn.send("\r")
time.sleep(5)
output = remote_conn.recv(50000)
print(output)
remote_conn.send("conf t" + "\n")
remote_conn.send("voice-card" + " " + voicecard + "\n")
remote_conn.send("dsp services dspfarm\n")
remote_conn.send("exit\n")
remote_conn.send("dspfarm profile 1 conference security\n")
remote_conn.send("trustpoint CFBROUTER\n")
remote_conn.send("codec g711ulaw\n")
remote_conn.send("codec g711alaw\n")
remote_conn.send("codec g729ar8\n")
remote_conn.send("codec g729abr8\n")
remote_conn.send("codec g729r8\n")
remote_conn.send("codec g729br8\n")
remote_conn.send("maximum sessions 5\n")
remote_conn.send("associate application SCCP\n")
remote_conn.send("no shut\n")
remote_conn.send("exit\n")
remote_conn.send("sccp local gigabitEthernet 0/0/0\n")
remote_conn.send("sccp ccm " + cucmIP + " " + "identifier 1 version 7.0 trustpoint" + " " + cucmHostName + domain + "\n")
remote_conn.send("sccp\n")
remote_conn.send("sccp ccm group 1\n")
remote_conn.send("bind interface GigabitEthernet" + gigInterface + "\n")
remote_conn.send("associate ccm 1 priority 1\n")
remote_conn.send("associate profile 1 register CFBROUTER\n")
remote_conn.send("dspfarm profile 1 conference security\n")
remote_conn.send("sh\n")
remote_conn.send("yes\n")
remote_conn.send("no sh\n")
remote_conn.send("do wr\n")
output = remote_conn.recv(50000000)
print(output)

import cucmAXLpost

print(" ")
print(" ")
print(" ")
print("Done!!")
