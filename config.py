
#!/bin/env python

"""
Version: 0.1
Author: vakalapa@cisco.com

Azure Automation Script


"""
from netmiko import ConnectHandler
import paramiko
import socket


#net_connect = ConnectHandler(device_type='cisco_xe', ip='13.82.88.252', username='azureuser', password='+Ciscolab123')
#net_connect.find_prompt()
#output = net_connect.send_command("show ip int brief")
#output = net_connect.send_config_set(conf)

conf_int2 = ['int gi2','no shu','ip addr dhcp']
conf_smart_lic = ['ip http client source-interface GigabitEthernet1',
				'service call-home',
				'call-home',
				'contact-email-addr nnnnnnnn@cisco.com',
				'mail-server x.x.x.x priority 1',
				' profile "FOO"',
				'active',
				'no destination transport-method email',
				'destination transport-method http',
				'destination address http https://XXXXXXXXXXX/its/service/oddce/services/DDCEService',
				'ip name-server 8.8.8.8',
				'license smart enable',
				'do license smart register idtoken XXXXXXXXXXXXXX',
				'platform hardware throughput level MB 2500'
			]


ipsec_config = '''

                crypto isakmp policy 1 
                 encr aes 256 
                 authentication pre-share
                crypto isakmp key cisco address 0.0.0.0  
                ! 
                crypto ipsec transform-set uni-perf esp-aes 256 esp-sha-hmac 
                 mode tunnel 
                ! 
                crypto ipsec profile vti-1 
                 set security-association lifetime kilobytes disable 
                 set security-association lifetime seconds 86400 
                 set transform-set uni-perf  
                 set pfs group2 
                ! 
                interface Tunnel1 
                 ip address {} 255.255.255.252 
                 load-interval 30 
                 tunnel source GigabitEthernet1 
                 tunnel mode ipsec ipv4 
                 tunnel destination {}
                 tunnel protection ipsec profile vti-1 
                ! 
'''

def get_pip_from_dns(dns):
	return socket.gethostbyname(dns)


def get_connect_obj(dns):
	pip = get_pip_from_dns(dns)
	return ConnectHandler(device_type='cisco_xe', ip=pip, username='azureuser', password='ANKJkjlsdvbjsadieponvnlsdnvie')

def configure_g2(connect_obj):	
	output = connect_obj.send_command("show ip int brief")
	print output
	output = connect_obj.send_config_set(conf_int2)
	print output
	output = connect_obj.send_command("show ip int brief")
	print output

def configure_ipsec(connect_obj,vm):
	dns = 'csr-1-gi1-pip-dns.eastus.cloudapp.azure.com'
	ip = '192.168.101.2'
	tunnel_route = 'ip route {} 255.255.255.248 tunn1'
	net = '10.20.0.16'
	if '1' in vm:
		dns = 'csr-2-gi1-pip-dns.eastus.cloudapp.azure.com'
		ip = '192.168.101.1'
		net = '10.20.0.32'
	pip = get_pip_from_dns(dns)
	new_ipsec_config = ipsec_config.format(ip,pip)
	print new_ipsec_config
	output = connect_obj.send_config_set(new_ipsec_config)
	print output
	tunnel_route = tunnel_route.format(net)
	output = connect_obj.send_config_set(tunnel_route)
	print output


def disconnect_device(connect_obj):
	connect_obj.disconnect()


def get_connect_obj_linux(dns):
	pip = get_pip_from_dns(dns)
	ssh = paramiko.SSHClient()
	ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
	ssh.connect(pip, username='azureuser', password='+Ciscolab123')
	return ssh


def excute_cmd(connect_obj, cmd):
	stdin, stdout, stderr =  connect_obj.exec_command(cmd)
	return stdin, stdout, stderr 


def disconnect_device_linux(connect_obj):
	connect_obj.close()









