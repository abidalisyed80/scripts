#!/usr/bin/env python3
#This script will check sysem load and disk usage for given patitions and notify via email using gmail smtp
#written by Abid Ali Syed (abid.ali.syed80@gmail.com )
import psutil
import socket
import subprocess
import emails
import os

# Function to get host FQDN and IP address
def get_host_info():
    hostname = socket.gethostname()
    fqdn = socket.getfqdn()
    ip = socket.gethostbyname(hostname)
    return fqdn, ip

# Get and print top 10 CPU consuming processes
def get_top_cpu_processes():
    command = "ps aux --sort=-%cpu | head -n 11"
    process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = process.communicate()
    if process.returncode != 0:
        raise Exception(f"Alert executing command: {stderr.decode()}")
    # Process the output
    output = stdout.decode().splitlines()
    return output

# Function to get disk usage details formatted like 'df -h' for specific partitions
def get_disk_usage_details():
    partitions_to_check = [
	'/', 
	'/disk1',
	'/data2'
	]
    usage_details = ["Filesystem      Size  Used Avail Use% Mounted on"]
    for partition in psutil.disk_partitions():
        if partition.mountpoint in partitions_to_check:
            usage = psutil.disk_usage(partition.mountpoint)
            usage_details.append(
                f"{partition.device:<15} {usage.total / (1024**3):>4.1f}G {usage.used / (1024**3):>4.1f}G {usage.free / (1024**3):>4.1f}G {usage.percent:>3}% {partition.mountpoint}"
            )
    return usage_details

# Function to check system health
def check_health():
    # Get host information
    host_fqdn, host_ip = get_host_info()

    # Check CPU usage
    cpu_usage = psutil.cpu_percent(interval=1)
    if cpu_usage > 80:
        top_processes = get_top_cpu_processes()
        for line in top_processes:
            print(line)
        emails.send_email(f"[{host_fqdn}] Alert - CPU usage is over 80%", "\n".join(top_processes))

    # Check load averages
    load1, load5, load15 = os.getloadavg()
    if load5 > 3:
        emails.send_email(f"[{host_fqdn}] Alert - Load average is over 3", f"Host: {host_fqdn} ({host_ip})\n\nAlert - 5-minute load average is over 3\n\nPlease check your system and resolve the issue as soon as possible.\n\nLoad averages: 1 min: {load1}, 5 min: {load5}, 15 min: {load15}")
    if load15 > 3:
        emails.send_email(f"[{host_fqdn}] Alert - Load average is over 3", f"Host: {host_fqdn} ({host_ip})\n\nAlert - 15-minute load average is over 3\n\nPlease check your system and resolve the issue as soon as possible.\n\nLoad averages: 1 min: {load1}, 5 min: {load5}, 15 min: {load15}")

    # Check disk space for specific partitions
    disk_usage_details = get_disk_usage_details()
    for detail in disk_usage_details:
        print(detail)
        if 'Used' not in detail:
            usage_percent = float(detail.split()[4][:-1])
            if usage_percent > 80:
                emails.send_email(f"[{host_fqdn}] Alert - Disk space usage over 80%", f"Host: {host_fqdn} ({host_ip})\n\nAlert - Disk space usage is over 80%\n\nDetails:\n{detail}\n\nPlease check your system and resolve the issue as soon as possible.")

    # Check available memory
    available_memory = psutil.virtual_memory().available / (1024 * 1024)  # in MB
    if available_memory < 100:
        emails.send_email(f"[{host_fqdn}] Alert - Available memory is less than 100MB", f"Host: {host_fqdn} ({host_ip})\n\nAlert - Available memory is less than 100MB\n\nPlease check your system and resolve the issue as soon as possible.")

    # Check hostname resolution
    try:
        socket.gethostbyname('localhost')
    except socket.gaierror:
        emails.send_email(f"[{host_fqdn}] Alert - localhost cannot be resolved to 127.0.0.1", f"Host: {host_fqdn} ({host_ip})\n\nAlert - localhost cannot be resolved to 127.0.0.1\n\nPlease check your system and resolve the issue as soon as possible.")

def main():
    check_health()

if __name__ == "__main__":
    main()

