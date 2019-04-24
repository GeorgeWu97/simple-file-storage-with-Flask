#! /usr/bin/env python3
# -*- coding:utf-8 -*-
from flask import Flask, render_template, abort, send_from_directory, request, redirect, url_for, g, flash, session
from werkzeug.utils import secure_filename
import os
from os import path, getcwd, mkdir, rmdir, remove, replace, listdir
import json

validtype = ['txt', 'pdf', 'doc', 'docx', 'bmp', 'jpg', 'jpeg', 'png', 'gif', 'cr2',
             'ppt', 'pptx', 'pps', 'ppsx', 'avi', 'mov', 'qt', 'asf', 'rm', 'mp4',
             'mp3', 'wav', 'xls', 'xlsx', 'zip', 'rar', '7z', 'iso', 'gz', 'z', 
             'ico', 'icon', 'html', 'css', 'js', 'py', 'c', 'cpp' ,'java']
def secure_path(path):
    item = path.strip().split('/')
    for name in item:
        if name == '..':
            return False
    return True
    
app = Flask('file_storage')
app.secret_key = 'some_secret'

@app.route('/')
def init():
    return render_template('base.html')

@app.route('/register', methods=('GET', 'POST'))
def register():
    """Register a new user.
    """
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        path = os.getcwd()
        error = None

        if not username:
            error = 'Username is required.'
        elif not password:
            error = 'Password is required.'
        else:
            if os.path.exists(path+'/'+username):
                error = 'Username  is already registered.'

        if error is None:
            # the name is available, store it in the database and go to
            # the login page
            os.makedirs(path+'/'+username+'/'+password)
            return redirect(url_for('login'))

        flash(error)

    return render_template('register.html')

@app.route('/login', methods=('GET', 'POST'))
def login():
    """Log in a registered user by adding the user id to the session."""
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        path = os.getcwd()
        error = None

        if not os.path.exists(path+'/'+username):
            error = 'Incorrect username.'
            session.clear()
   #     elif not check_password_hash(user[1], password):
        elif not os.path.exists(path+'/'+username+'/'+password):
            error = 'Incorrect password.'
            session.clear()
        if error is None:
            session.clear()
            session['user_id'] = username
            #g.user = session
            return redirect(url_for('index', path_name = username))
            #render_template('auth/Canteen_list.html')

            # return redirect(url_for('index'))


        flash(error)
        # print (g.user)
    return render_template('login.html')

@app.route('/logout')
def logout():
    """Clear the current session, including the stored user id."""
    session.clear()
    return redirect(url_for('login'))

@app.route('/dir_index/<path:path_name>')
def index(path_name):
    while path_name[-1] == '/': path_name = path_name[:-1]
    def get_type(type):
        type = type.lower()[1:]
        if type in ['txt', 'pdf', 'iso']: return type
        if type in ['doc', 'docx']: return 'word'
        if type in ['bmp', 'jpg', 'jpeg', 'png', 'gif', 'cr2', 'ico', 'icon']: return 'image'
        if type in ['ppt', 'pptx', 'pps', 'ppsx']: return 'ppt'
        if type in ['avi', 'mov', 'qt', 'asf', 'rm', 'mp4']: return 'video'
        if type in ['mp3', 'wav']: return 'music'
        if type in ['xls', 'xlsx']: return 'excel'
        if type in ['zip', 'rar', '7z', 'gz', 'z']: return 'compression'
        return 'file'
        
    path = os.getcwd() + '/' + path_name    
    fd_list = os.listdir(path)
    index_list = []
    idx = 1
    for file in fd_list:
        if os.path.isfile(path + '/' + file):
            name, type = os.path.splitext(file)
            index_list.append([file, name, type[1:], get_type(type), idx])
        else:
            index_list.append([file, file, 'dir', 'folder', idx])
            
        idx += 1
   
    return render_template('index.html', list = index_list, path = path_name)

@app.route('/download/<path:file_path>')
def download(file_path):
    if not secure_path(file_path): abort(405)
    while file_path[-1]=='/': file_path = file_path[:-1]
    dir_path = os.getcwd()
    if os.path.isfile(dir_path + '/' + file_path):
        return send_from_directory(dir_path, file_path, as_attachment=True)
    abort(404)

@app.route('/upload/<path:dir_path>', methods=['POST'])    
def upload(dir_path):
    if not secure_path(dir_path): abort(405)
    f = request.files['file']
    
    def valid_file(name):
        ext = name.rsplit('.',1)[1].lower()
        return (ext in validtype) and (secure_path(name))
        
    if f and valid_file(f.filename):
        fname=secure_filename(f.filename)
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)

        f.save(os.path.join(dir_path,fname))
        return json.dumps({'code':200,'url':url_for('index',path_name=dir_path, _external=True)})
    else: abort(405)

@app.route('/delete/<path:file_path>')
def delete(file_path):
    if not secure_path(file_path): abort(405)
    while file_path[-1]=='/': file_path = file_path[:-1]
    root_dir = os.getcwd()
    target_path = root_dir + '/' + file_path
    if os.path.exists(target_path):
        del_rec(target_path)
        # return json.dumps({'code':200,'url':url_for('index',path_name=file_path, _external=True)})
        return redirect(url_for('index', path_name = parent(file_path)))
    else: abort(404)

def del_rec(str):
    if path.exists(str):
        if path.isfile(str):
            try:
                remove(str)
            except OSError as err:
                print(err)
        else:
            try:
                file_list = listdir(str)
                for file in file_list:
                    str1 = str + '/' + file
                    del_rec(str1)                  
                rmdir(str)
            except OSError as err:
                print(err)
                
def parent(str):
    k = len(str) - 1
    while (k > 0) and (str[k] != '/'):
        k = k - 1
    return str[0:k]
        
               
if __name__ == '__main__':
    app.run(host = '127.0.0.1', port = '8080', debug = True)
    
