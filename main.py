
#!/bin/env python

"""
Version: 0.1
Author: vakalapa@cisco.com

Azure Automation Script


"""


from utility import *
import re
import sys
import time
import ipaddress

from config import *

from azure.common.credentials import ServicePrincipalCredentials
from azure.mgmt.resource import ResourceManagementClient
from azure.mgmt.storage import StorageManagementClient
from azure.mgmt.network import NetworkManagementClient
import azure.mgmt.network
from azure.storage import CloudStorageAccount
from azure.storage.blob.models import ContentSettings, PublicAccess
from azure.mgmt.compute.compute import ComputeManagementClient
from msrestazure.azure_exceptions import CloudError

#credentials = UserPassCredentials('vakalapa@cisco.com', '')
subscription_id = 'XXXXXXXXXXXX'


credentials = ServicePrincipalCredentials(
	client_id = 'XXXXXXXXXXXX',
	secret = 'XXXXXXXXXXXX',
	tenant = 'XXXXXXXXXXXX'
)

resource_client = ResourceManagementClient(credentials, subscription_id)
storage_client = StorageManagementClient(credentials, subscription_id)
compute_client = ComputeManagementClient(credentials, subscription_id)
network_client = NetworkManagementClient(credentials, subscription_id)
resource_group_name = 'my_resource_group'
storage_account_name = 'myuniquestorageaccount'
'''
resource_client.resource_groups.create_or_update(
									resource_group_name,
										{
											'location':'westus'
										}
									)
'''

VM_REFERENCE = {
	'linux': {
		'publisher': 'Canonical',
		'offer': 'UbuntuServer',
		'sku': '16.04.0-LTS',
		'version': 'latest'
	},
	'csr': {
		'publisher': 'cisco',
		'offer': 'cisco-csr-1000v',
		'sku': None,
		'version': None
	}
}

def create_RG(rg,location):
	resource_client.resource_groups.create_or_update(
		rg, 
		{
			'location': 
			location
		}
	)
	print msg_color('[INFO] Created RG: {} in {}'.format(rg,location),'green')
	return True
def create_vnet(rg,location,vnetname, net_addr):
	try:
		async_vnet_creation = network_client.virtual_networks.create_or_update(
			rg,
			vnetname,
			{
				'location': location,
				'address_space': {
					'address_prefixes': [str(net_addr)]
				}
			}
		)
		async_vnet_creation.wait()
		print msg_color('[INFO] Created VNET: {} in {}'.format(vnetname,location),'green')
	except CloudError as e:
			print msg_color('[WARNING] {}'.format(e),'fail') 


def create_subnets(rg,location,vnetname, subnet_dict):
	subnet_obj_dict = {}
	for key,val in subnet_dict.items():
		rt = None
		param = {'address_prefix': str(val)}
		if '2' in key:
			rt = '/subscriptions/dbc54458-4bea-4004-8ad5-56b7fc6fb876/resourceGroups/test/providers/Microsoft.Network/routeTables/csr-rt-1'
			param = {'address_prefix': str(val),
				'route_table' : { 'id': rt}
				}
		elif '4' in key:
			rt = '/subscriptions/dbc54458-4bea-4004-8ad5-56b7fc6fb876/resourceGroups/test/providers/Microsoft.Network/routeTables/csr-rt-2'
			param = {'address_prefix': str(val),
				'route_table' : { 'id': rt}
				}
		try:
			async_subnet_creation = network_client.subnets.create_or_update(
				rg,
				vnetname,
				key,
				param
			)
			subnet_info = async_subnet_creation.result()
			subnet_obj_dict[subnet_info.name] = subnet_info
			print msg_color('[INFO] Created subnet: {} with {}'.format(subnet_info.name,subnet_info.address_prefix),'green') 
		except CloudError as e:
			print msg_color('[WARNING] {}'.format(e),'fail') 
	return subnet_obj_dict

def create_network_interface(region, group_name, interface_name,
		network_name, subnet_name, pip):

	result = network_client.subnets.get(group_name, network_name, subnet_name)
	subnet = result.id
	if pip:
		pip_name = interface_name + '-pip'
		'''
		result = network_client.public_ip_addresses.create_or_update(
			group_name,
			ip_name,
			azure.mgmt.network.PublicIpAddress(
				location=region,
				public_ip_allocation_method='Dynamic',
				idle_timeout_in_minutes=4,
			),
		)
		print result
		print result.__dict__
		'''
		public_ip_parameters = {
			'location': region,
			'public_ip_allocation_method': 'static',
			'dns_settings': {
				'domain_name_label': (pip_name + '-dns').lower()
			},
			'idle_timeout_in_minutes': 30
		}

		async_publicip_creation = network_client.public_ip_addresses.create_or_update(
			group_name,
			pip_name,
			public_ip_parameters
		)
		public_ip_info = async_publicip_creation.result()
		#print public_ip_info
		#print public_ip_info.__dict__

		#print subnet
		result = network_client.network_interfaces.create_or_update(
			group_name,
			interface_name,
			{
				'location' : region,
				'enable_ip_forwarding' : True,
				'ip_configurations' : [
					{
						'name': 'IP_CONFIG_NAME',						
						'private_ip_allocation_method': 'Dynamic',
						'subnet' : {
							'id' : subnet
						},
						'public_ip_address': {
							'id': public_ip_info.id
						}
					},
				],
			}
		)
	else:
		#print subnet
		result = network_client.network_interfaces.create_or_update(
			group_name,
			interface_name,
			{
				'location' : region,
				'enable_ip_forwarding': True,
				'ip_configurations' : [
					{
						'name': 'IP_CONFIG_NAME',
						'subnet' : {
							'id' : subnet
						}
					},
				],
			}
		)

	result = network_client.network_interfaces.get(
		group_name,
		interface_name
	)
	#import pdb;pdb.set_trace()
	print msg_color('[INFO] Created {} nic'.format(result.name),'green')
	return result.id

def update_route_table(region, group_name):
	result = network_client.route_tables.create_or_update()


def create_vm_parameters(vmname, location, uname, password, nic_id_1, nic_id_2, vm_reference):
	"""Create the VM parameters structure.
	"""
	return {
		'location': location,
		'os_profile': {
			'computer_name': vmname,
			'admin_username': uname,
			'admin_password': password
		},
			'hardware_profile': {
			'vm_size': 'Standard_DS2_v2'
		},
		'storage_profile': {
			'image_reference': {
				'publisher': vm_reference['publisher'],
				'offer': vm_reference['offer'],
				'sku': vm_reference['sku'],
				'version': 'latest'
			},
		},
		'plan' : {
			'name' : vm_reference['sku'],
			'publisher' : vm_reference['publisher'],
			'product' : vm_reference['offer']
		},
		'network_profile': {
			'network_interfaces': [{
				'id': nic_id_1,
				'primary' : True
			},{
				'id': nic_id_2,
				'primary' : False
			}]
		},
	}

def create_nics(vm_list, subnet_obj_dict, rg, location, vnet_name):

	for vm,val in vm_list.items():
		print msg_color('[INFO] Working on {} vm'.format(vm),'green')
		#print 
		for nic, nic_val in  val['nic'].items():
			nic_name = vm + '-' + nic
			pip = False
			if 'gi1' in nic_name.lower():
				pip = True
			nic_id = create_network_interface(location, rg, nic_name,vnet_name, nic_val['subnetname'], pip)
			vm_list[vm]['nic'][nic]['id'] = nic_id
			if pip:
				vm_list[vm]['nic'][nic]['dns'] = nic_name + '-pip-dns.' + location + '.cloudapp.azure.com'

def create_vms(vm_list, rg, location):
	uname ='azureuser'
	password = 'ANKJkjlsdvbjsadieponvnlsdnvie'
	for vm,val in vm_list.items():
		#print 
		if 'csr' in vm.lower():
			#create_csr_vm(rg, location, vm, val)
			vm_parameters = create_vm_parameters(vm, location, uname, password, val['nic']['gi1']['id'], val['nic']['gi2']['id'], VM_REFERENCE['csr'])
		else:
			vm_parameters = create_vm_parameters(vm, location, uname, password, val['nic']['gi1']['id'], val['nic']['gi2']['id'], VM_REFERENCE['linux'])
			del vm_parameters['plan']
		print vm_parameters
		#'''
		async_vm_creation = compute_client.virtual_machines.create_or_update(
								rg, vm, vm_parameters
							)

		print vm_parameters

		print msg_color('[INFO] Creating {} vm'.format(vm),'green')
		async_vm_creation.wait()
		#'''
		print msg_color('[INFO] Creating {} vm'.format(vm),'green')


def get_csr_skus(location):
	try:
		skus = compute_client.virtual_machine_images.list_skus(location,'cisco','cisco-csr-1000v')
	except CloudError as e:
		print e
		sys.exit(1)
	return [i.name for i in skus]

def get_image(location, sku):
	skus = compute_client.virtual_machine_images.list(location,'cisco','cisco-csr-1000v',sku)
	#print skus
	return [i.name for i in skus]

def do_interactive():
	ipsec = False
	print msg_color("Hello there. Let's start setting up your environment",'header')
	if confirm(msg_color('Do you want to run IPSEC test? (y/n): ','bold')):
		print msg_color('[INFO] RUNNING IPSEC with below topology','green')
		ipsec = True
		print '''
 ________     ________               ________     ________
|        |   |        |             |        |   |        |
| LINUX1 | --|  CSR1  |  -- IPSEC --|  CSR2  |-- | LINUX2 |
|________|   |________|             |________|   |________|
		'''
	location = read_line(msg=msg_color('Where do you want the setup? Ex: eastus, westus: ','bold'))
	sku = read_line(msg=msg_color('\nWhich Version of CSR do you want from below? \n{}: '.format(str(get_csr_skus(location))),'bold'))
	version = str(get_image(location,sku)[0])
	print msg_color('[INFO] Using image {} for CSR'.format(version),'green')

	VM_REFERENCE['csr']['sku'] = sku
	VM_REFERENCE['csr']['version'] = version
	rg = read_line(msg=msg_color('\nResource Group name: ','bold'))
	create_RG(rg,location)
	vnet_name = read_line(msg=msg_color('\nName of VNET: ','bold'))
	net_addr = read_line(msg=msg_color('\nAddress space for VNET, ex: 10.20.0.0/16 [Press enter for default]: ','bold'))
	if not net_addr:
		net_addr = ipaddress.ip_network(unicode('10.20.0.0/16'))
	else:
		net_addr = ipaddress.ip_network(net_addr)
	print net_addr
	create_vnet(rg,location,vnet_name,net_addr)
	subnet_mask = read_line(msg=msg_color('\nMask for subnets?: ','bold'))
	number_of_subnets= int(read_line(msg=msg_color('\nHow many subnets do you want?: ','bold')))
	if ipsec and (number_of_subnets < 6):
		print msg_color('[WARNING] NEED 6 subnets for IPSEC case. Only {} are provided.'.format(number_of_subnets),'fail')
		number_of_subnets = 6
	subnet_dict = {}
	temp_num = 0
	for subnet in net_addr.subnets(new_prefix=int(subnet_mask)):
		if temp_num >= number_of_subnets:
			continue
		name = 'subnet-{}'.format(temp_num)
		subnet_dict[name] = subnet
		temp_num += 1

	#print subnet_dict
	subnet_obj_dict = create_subnets(rg,location,vnet_name, subnet_dict)

	vm_list = {
		'CSR-1' : {
			'nic' : {
				'gi1' : {
					'subnetname' : 'subnet-1'
				},
				'gi2' : {
					'subnetname' : 'subnet-2'
				}
			}
		},
		'CSR-2' : {
			'nic' : {
				'gi1' : {
					'subnetname' : 'subnet-3'
				},
				'gi2' : {
					'subnetname' : 'subnet-4'
				}
			}
		},
		'linux-1' : {
			'nic' : {
				'gi1' : {
					'subnetname' : 'subnet-5'
				},
				'gi2' : {
					'subnetname' : 'subnet-2'
				}
			}
		},
		'linux-2' : {
			'nic' : {
				'gi1' : {
					'subnetname' : 'subnet-0'
				},
				'gi2' : {
					'subnetname' : 'subnet-4'
				}
			}
		}
	}
	
	create_nics(vm_list, subnet_obj_dict, rg, location, vnet_name)
	#'''
	print vm_list
	create_vms(vm_list, rg, location)
	#'''
	for vm in vm_list.keys():
		if 'csr' in vm.lower():
			vm_list[vm]['connect_obj'] = get_connect_obj(vm_list[vm]['nic']['gi1']['dns'])		
			configure_g2(vm_list[vm]['connect_obj'])
			configure_ipsec(vm_list[vm]['connect_obj'], vm)
			disconnect_device(vm_list[vm]['connect_obj'])
		else:
			vm_list[vm]['connect_obj'] = get_connect_obj_linux(vm_list[vm]['nic']['gi1']['dns'])		
			stdin, stdout, stderr  = excute_cmd(vm_list[vm]['connect_obj'], 'uptime')
			print stdout.readlines() 	
			stdin, stdout, stderr  = excute_cmd(vm_list[vm]['connect_obj'], 'sudo apt-get install iperf3 -y')
			print stdout.readlines() 
			#disconnect_device_linux(vm_list[vm]['connect_obj'])
	#'''

	print msg_color('\n\n[INFO] STARTING IPERF TEST','green')

	stdin, stdout, stderr  = excute_cmd(vm_list['linux-2']['connect_obj'], 'iperf3 -s -D')
	#print stdout.readlines() 

	stdin, stdout, stderr  = excute_cmd(vm_list['linux-1']['connect_obj'], 'iperf3 -c 10.20.0.36 -M 1400 -t 20 > test.txt &')
	#print stdout.readlines()
	#print a
	time.sleep(40)
	stdin, stdout, stderr  = excute_cmd(vm_list['linux-1']['connect_obj'], 'cat test.txt')
	data =  stdout.readlines()
	#print data
	thr = None
	for a in data:
		print a
		if 'sender' in a:
			thr = a
			#print thr

	regex = r"([0-9]+) Mbits"
	b = re.search(regex,thr)
	print msg_color('\n\n[INFO] Throughput achieved is {}'.format(b.group()),'green')



	disconnect_device_linux(vm_list['linux-2']['connect_obj'])
	disconnect_device_linux(vm_list['linux-1']['connect_obj'])


if __name__ == '__main__': # pragma: no cover
	do_interactive()


