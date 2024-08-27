#!/usr/bin/env python3
#This script will sync source and backup folders using multiprocess 
#written by Abid Ali Syed (abid.ali.syed80@gmail.com )
import os
from multiprocessing import Pool
import subprocess

src = os.path.expanduser("/data/nas-2/VMBackup/")
dest = os.path.expanduser("/usbmount/VMBackup/")

def get_pathlist(folder):
    pathlist = []

    for root, dirs, files in os.walk(folder):
        path = os.path.relpath(root, folder)
        if dirs != []:
            for d in dirs:
                pathlist.append((path, d))
        for f in files:
            pathlist.append((path, f))

    return pathlist

def backup(path):
    source = os.path.join(src, path[0], path[1])
    destination = os.path.join(dest, path[0])
    subprocess.call(['rsync', '-avht', '--progress', source, destination])

if __name__ == "__main__":
    src_pathlist = get_pathlist(src)

    if src_pathlist:
        pool = Pool(len(src_pathlist), maxtasksperchild=2)
        pool.map(backup, src_pathlist)
        pool.close()
        pool.join()
    else:
        print("No files or directories found in the source directory.")


