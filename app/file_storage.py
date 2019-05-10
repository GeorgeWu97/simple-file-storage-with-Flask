#! /usr/bin/env python3
# -*- coding:utf-8 -*-
from flask import Flask, render_template, abort, send_from_directory, request, redirect, url_for, g, flash, session, make_response
from werkzeug.utils import secure_filename
from werkzeug.urls import url_quote
import os
from os import path, getcwd, mkdir, rmdir, remove, replace, listdir
import json
import time as t
from function import *
    
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
        path = getcwd()
        error = None

        if not username:
            error = 'Username is required.'
        elif not password:
            error = 'Password is required.'
        else:
            if path.exists(path+'/'+username):
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
        path = getcwd()
        error = None

        if not path.exists(path+'/'+username):
            error = 'Incorrect username.'
            session.clear()
   #     elif not check_password_hash(user[1], password):
        elif not path.exists(path+'/'+username+'/'+password):
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
    while path_name[-1]=='/': path_name = path_name[:-1]
    dpath = getcwd() + '/' + path_name   
    index_list, size, time = dirsearch(dpath, path_name)
    return render_template('index.html', list = index_list, path = path_name)

@app.route('/download/<path:file_path>')
def download(file_path):
    if not secure_path(file_path): abort(405)
    while file_path[-1]=='/': file_path = file_path[:-1]
    dir_path = getcwd()
    if path.isfile(dir_path + '/' + file_path):
        dirpath, filename = path.split(dir_path + '/' + file_path)
        response = make_response(send_from_directory(dirpath, filename, as_attachment=True))
        response.headers["Filename"] = url_quote(filename)
        return response
    abort(404)

@app.route('/upload/<path:dir_path>', methods=['POST'])    
def upload(dir_path):             
    if not secure_path(dir_path): abort(405)
    f = request.files['file']
            
    if f and valid_file(f.filename):
        while (dir_path[-1] == '/'): dir_path = dir_path[:-1]
        if not path.exists(dir_path):
            os.makedirs(dir_path)
        
        id = 1
        name, type = path.splitext(f.filename)
        type = type[1:]
        rn = name
        while path.exists(path.join(dir_path,f.filename)):
            f.filename = rn + '(%d)'%id + '.' + type
            id += 1
            
        f.save(path.join(dir_path,f.filename))
        pathn = dir_path + '/' + f.filename
        name, type = path.splitext(f.filename)
        fclass = get_type(type)
        size = normalsize(path.getsize(pathn))
        time = TimeStampToTime(path.getmtime(pathn))
        return json.dumps({'code':200, 'class':fclass, 'fn':f.filename, 'name':name, 
                           'type':type[1:], 'size':size, 'time':time})
    else: abort(405)

@app.route('/newfolder/<path:dir_path>', methods=['POST'])
def createfolder(dir_path):
    while dir_path[-1]=='/': dir_path = dir_path[:-1]
    dirname = request.json.get('name')
    root_dir = getcwd()
    oname = dirname
    id = 1
    while path.exists(root_dir+'/'+dir_path+'/'+dirname): 
        dirname = oname+'(%d)'%id
        id += 1
    mkdir(root_dir+'/'+dir_path+'/'+dirname)
    return json.dumps({'code':200, 'dn':dirname})
    
@app.route('/delete/<path:file_path>', methods=["DELETE"])
def delete(file_path):                
    if not secure_path(file_path): abort(405)
    while file_path[-1]=='/': file_path = file_path[:-1]
    root_dir = getcwd()
    target_path = root_dir + '/' + file_path
    if path.exists(target_path):
        del_rec(target_path)
        # return json.dumps({'code':200,'url':url_for('index',path_name=file_path, _external=True)})
        return json.dumps({'code':200});
    else: abort(404)

               
if __name__ == '__main__':
    app.run(host = '127.0.0.1', port = '8080', debug = True)
    
