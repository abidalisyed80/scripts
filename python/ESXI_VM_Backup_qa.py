#!/usr/bin/env python3
#This script will backup all VMs(name starting with 'qa') from ESXi host and save on local sysetem
#Written by Abid Ali Syed (abid.ali.syed80@gmail.com)
from pyVim.connect import SmartConnect, Disconnect
from pyVmomi import vim
import ssl
import atexit
import os
import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning

# Suppress the InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

def get_obj(content, vimtype, name):
    obj = None
    container = content.viewManager.CreateContainerView(content.rootFolder, vimtype, True)
    for c in container.view:
        if c.name == name:
            obj = c
            break
    return obj

def power_off_vm(vm):
    if vm.runtime.powerState == vim.VirtualMachinePowerState.poweredOn:
        print(f"Powering off VM: {vm.name}")
        task = vm.PowerOffVM_Task()
        while task.info.state == vim.TaskInfo.State.running:
            continue
        if task.info.state == vim.TaskInfo.State.success:
            print(f"VM {vm.name} powered off successfully.")
        else:
            raise Exception(f"Failed to power off VM {vm.name}: {task.info.error.msg}")
    else:
        print(f"VM {vm.name} is already powered off, skipping power off step.")

def power_on_vm(vm):
    if vm.runtime.powerState == vim.VirtualMachinePowerState.poweredOff:
        print(f"Powering on VM: {vm.name}")
        task = vm.PowerOnVM_Task()
        while task.info.state == vim.TaskInfo.State.running:
            continue
        if task.info.state == vim.TaskInfo.State.success:
            print(f"VM {vm.name} powered on successfully.")
        else:
            raise Exception(f"Failed to power on VM {vm.name}: {task.info.error.msg}")

def create_snapshot(vm, snapshot_name, description):
    task = vm.CreateSnapshot_Task(name=snapshot_name, description=description, memory=False, quiesce=True)
    return task

def export_ovf(si, vm, local_backup_path):
    if local_backup_path is None:
        raise ValueError("local_backup_path cannot be None")

    print(f"Exporting VM {vm.name} to {local_backup_path}...")

    ovf_manager = si.content.ovfManager
    lease = vm.ExportVm()

    while lease.state == vim.HttpNfcLease.State.initializing:
        continue
    
    if lease.state != vim.HttpNfcLease.State.ready:
        raise Exception("Lease not ready, cannot export OVF/OVA.")
    
    # Create VM-specific backup directory if it doesn't exist
    vm_backup_path = os.path.join(local_backup_path, vm.name)
    print(f"Creating VM-specific directory: {vm_backup_path}")
    
    if not os.path.exists(vm_backup_path):
        os.makedirs(vm_backup_path)
    
    # Download the OVF descriptor and all associated files
    for deviceUrl in lease.info.deviceUrl:
        print(f"Processing device URL: {deviceUrl.url}")
        print(f"deviceUrl.targetId: {deviceUrl.targetId}")

        if deviceUrl.targetId is None:
            print("Warning: deviceUrl.targetId is None, skipping this device URL.")
            continue

        url = deviceUrl.url.replace("*", esxi_host)
        file_name = os.path.join(vm_backup_path, os.path.basename(deviceUrl.targetId))
        
        print(f"Downloading {file_name} from {url}")
        
        with open(file_name, 'wb') as f:
            r = requests.get(url, stream=True, verify=False)
            for chunk in r.iter_content(chunk_size=1024):
                if chunk:
                    f.write(chunk)

    lease.HttpNfcLeaseComplete()
    print(f"Exported OVF and all related files for VM {vm.name} to {vm_backup_path}")

def backup_vm(si, vm_name, snapshot_name, description, local_backup_path):
    print(f"Starting backup for VM: {vm_name} to path: {local_backup_path}")

    if local_backup_path is None:
        raise ValueError("local_backup_path cannot be None")

    content = si.RetrieveContent()
    vm = get_obj(content, [vim.VirtualMachine], vm_name)
    
    if not vm:
        print(f"VM {vm_name} not found!")
        return
    
    # Power off the VM if it's powered on
    power_off_vm(vm)

    print(f"Creating snapshot for VM: {vm_name}")
    snapshot_task = create_snapshot(vm, snapshot_name, description)
    
    while snapshot_task.info.state == vim.TaskInfo.State.running:
        continue
    
    if snapshot_task.info.state == vim.TaskInfo.State.success:
        print(f"Snapshot {snapshot_name} created successfully for VM: {vm_name}")
        export_ovf(si, vm, local_backup_path)
        print(f"Backup for VM {vm_name} completed successfully.")
    else:
        print(f"Failed to create snapshot: {snapshot_task.info.error.msg}")
    
    # Power on the VM after the backup is completed
    power_on_vm(vm)

def main():
    # Connection details for remote ESXi host
    global esxi_host
    esxi_host = 'esxi_host_ip'
    username = 'username'
    password = 'your_password'
    port = 443

    # Base backup path
    base_backup_path = '/data/s3/esxi-backup'

    # Directories for dev and non-dev backups
    dev_backup_path = os.path.join(base_backup_path, 'dev_backups')
    non_dev_backup_path = os.path.join(base_backup_path, 'non_dev_backups')

    # Ensure backup directories exist
    for path in [dev_backup_path, non_dev_backup_path]:
        if not os.path.exists(path):
            print(f"Creating backup directory: {path}")
            os.makedirs(path)

    # Disable SSL certificate verification (useful in dev environments)
    context = ssl._create_unverified_context()

    si = SmartConnect(host=esxi_host, user=username, pwd=password, port=port, sslContext=context)
    
    atexit.register(Disconnect, si)
    
    # VM details - retrieve all VMs
    content = si.RetrieveContent()
    vm_names = [vm.name for vm in content.viewManager.CreateContainerView(content.rootFolder, [vim.VirtualMachine], True).view]

    # Backup VMs based on their name
    snapshot_name = 'Backup_Snapshot'
    description = 'Snapshot for backup'

    for vm_name in vm_names:
        if vm_name.lower().startswith('qa'):
            print(f"Backing up dev VM: {vm_name}")
            backup_vm(si, vm_name, snapshot_name, description, dev_backup_path)
if __name__ == "__main__":
    main()
