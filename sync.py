import paramiko
from flask import Flask, render_template, abort, send_from_directory, request, redirect, url_for, g, flash, session
from werkzeug.utils import secure_filename
import os
from os import path, getcwd, mkdir, rmdir, remove, replace, listdir
import json
import time as t

def login(ip,username,password,port = 22):
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(hostname = ip,port = port,username = username,password = password)
    return ssh

def synchronize(sftp, dir_path, timestamp):
    try:
        if path.exists(dir_path):
            sftp.mkdir("share/" + dir_path)
            fl = listdir(dir_path)
            for f in fl:
                str = dir_path + '/' + f
                if path.isfile(str):
                    info = os.stat(str)
                    if (info.st_mtime >= timestamp) or (info.st_ctime >= timestamp):
                        sftp.put(str, "share/" + str)
                else:
                    synchronize(sftp, str, timestamp)
                    
    except OSError as err:
        abort(405)

def main():
    ip = '10.128.206.15'
    username = 'student'
    password = '31415926'
    ssh = login(ip,username,password)
    sftp = ssh.open_sftp()
    synchronize(sftp, "file-storage", 0)
    sftp.close()
    
if __name__ == '__main__':
    main()

