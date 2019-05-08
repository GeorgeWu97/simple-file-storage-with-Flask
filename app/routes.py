from app import app
from flask import Flask, render_template, abort, send_from_directory, request, redirect, url_for, g, flash, session
from app.forms import LoginForm, RegistrationForm
from flask_login import current_user, login_user, login_required, logout_user
from app.models import User
from app import db, login
import os
from os import path, getcwd, mkdir, rmdir, remove, replace, listdir
import json
import time as t
from werkzeug.utils import secure_filename

def secure_path(path):
    return (path.find('..') == -1)

@app.route('/')
def init():
    return render_template('base.html')

@login.user_loader
def load_user(id):
    return User.query.get(int(id))

@app.before_request
def before_request():
    g.user = current_user

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    # if form.validate_on_submit():
    #     flash('Login requested for user {}, remember_me={}'.format(
    #         form.username.data, form.remember_me.data))
    #     return redirect('/login')
    # return render_template('login.html', title='Sign In', form=form)

    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password')
            return redirect(url_for('login'))
        login_user(user, remember=form.remember_me.data)
        user_path = 'users/' + form.username.data
        print (user_path)
        return redirect(url_for('index', path_name=user_path))
    return render_template('login.html', title='Sign In', form=form)


@app.route('/register', methods=['GET', 'POST'])
def register():
	path = os.getcwd()
	if current_user.is_authenticated:
		return redirect('/')
	form = RegistrationForm()
	if form.validate_on_submit():
		user = User(username=form.username.data)
		user.set_password(form.password.data)
		db.session.add(user)
		db.session.commit()
		os.makedirs(path+'/users/'+form.username.data)
		flash('Congratulations, you are now a registered user!')
		return redirect(url_for('login'))
	return render_template('register.html', form=form)

@login_required
@app.route('/logout')
def logout():
	logout_user()
	session.clear()
	# print(current_user.username)
	return redirect(url_for('login'))

@login_required
@app.route('/dir_index/<path:path_name>')
def index(path_name):
    while path_name[-1] == '/': path_name = path_name[:-1]
    dir_items = path_name.split('/')
    if len(dir_items) < 2:
    	print('Wrong URL')
    	return redirect('/')
    if dir_items[0] != 'users' or dir_items[1] != current_user.username:
    	print (dir_items[0])
    	print (dir_items[1])
    	print('This directory is not accessible for you. Please login again')
    	return redirect('/logout')
    	
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
    
    def normalsize(s):
        nexts = {'B':'K', 'K':'M', 'M':'G', 'G':'T'}
        ns = 'B'
        while s >=1024:
            s /= 1024
            ns = nexts[ns]
            
        return "%.4f"%s+ns
        
    def dirsearch(str):
        size = 0
        time = 0
        if os.path.exists(str):
            if path.isfile(str):
                try:
                    return path.getsize(str), path.getmtime(str)
                except OSError as err:
                    abort(405)
            else:
                try:
                    file_list = listdir(str)
                    for file in file_list:
                        s, t = dirsearch(str + '/' + file)                  
                        size += s
                        time = max(time, t)
                    return size, time
                except OSError as err:
                    abort(405)
        return size,time 
    
    def TimeStampToTime(timestamp):
        timestruct = t.localtime(timestamp)
        return t.strftime('%Y-%m-%d %H:%M:%S',timestruct)

    cpath = getcwd() + '/' + path_name    
    fd_list = listdir(cpath)
    index_list = []
    idx = 1
    for file in fd_list:
        if path.isfile(cpath + '/' + file):
            size = normalsize(path.getsize(cpath + '/' + file))
            time = TimeStampToTime(path.getmtime(cpath + '/' + file))
            name, type = path.splitext(file)
            index_list.append([name, type[1:], get_type(type), idx, size, time])
        else:
            size, time = dirsearch(cpath+ '/' + file)
            size = normalsize(size)
            if time == 0 : time = '-------------------------'
            else: time = TimeStampToTime(time)
            index_list.append([file, 'dir', 'folder', idx, size, time])
            
        idx += 1
   
    return render_template('index.html', list = index_list, path = path_name)

@login_required
@app.route('/download/<path:file_path>')
def download(file_path):
    if not secure_path(file_path): abort(405)
    while file_path[-1]=='/': file_path = file_path[:-1]
    dir_path = getcwd()
    if path.isfile(dir_path + '/' + file_path):
        return send_from_directory(dir_path, file_path, as_attachment=True)
    abort(404)

@login_required
@app.route('/upload/<path:dir_path>', methods=['POST'])    
def upload(dir_path):
    if not secure_path(dir_path): abort(405)
    f = request.files['file']
    validtype = ['txt', 'pdf', 'doc', 'docx', 'bmp', 'jpg', 'jpeg', 'png', 'gif', 'cr2',
             'ppt', 'pptx', 'pps', 'ppsx', 'avi', 'mov', 'qt', 'asf', 'rm', 'mp4',
             'mp3', 'wav', 'xls', 'xlsx', 'zip', 'rar', '7z', 'iso', 'gz', 'z', 
             'ico', 'icon', 'html', 'css', 'js', 'py', 'c', 'cpp' ,'java']     
    def valid_file(name):
        ext = name.rsplit('.',1)[1].lower()
        return (ext in validtype) and (name.find('\\')==-1 and name.find('/')==-1)
        
    if f and valid_file(f.filename):
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)

        f.save(path.join(dir_path,f.filename))
        return json.dumps({'code':200,'url':url_for('index',path_name=dir_path)})
    else: abort(405)

@login_required
@app.route('/newfolder/<path:dir_path>', methods=['POST'])
def createfolder(dir_path):
    while dir_path[-1]=='/': dir_path = dir_path[:-1]
    dirname = request.json.get('name')
    root_dir = getcwd()
    oname = dirname
    id = 1
    while os.path.exists(root_dir+'/'+dir_path+'/'+dirname): 
        dirname = oname+'(%d)'%id
        id += 1
    mkdir(root_dir+'/'+dir_path+'/'+dirname)
    return json.dumps({'code':200, 'url':url_for('index', path_name = dir_path)})

@login_required   
@app.route('/delete/<path:file_path>')
def delete(file_path):
    def del_rec(str):
        if os.path.exists(str):
            if path.isfile(str):
                try:
                    remove(str)
                except OSError as err:
                    abort(405)
            else:
                try:
                    file_list = listdir(str)
                    for file in file_list:
                        str1 = str + '/' + file
                        del_rec(str1)                  
                    rmdir(str)
                except OSError as err:
                    abort(405)
                    
    def parent(str):
        k = len(str) - 1
        while (k > 0) and (str[k] != '/'):
            k = k - 1
        return str[0:k]                
        
    if not secure_path(file_path): abort(405)
    while file_path[-1]=='/': file_path = file_path[:-1]
    root_dir = getcwd()
    target_path = root_dir + '/' + file_path
    if os.path.exists(target_path):
        del_rec(target_path)
        # return json.dumps({'code':200,'url':url_for('index',path_name=file_path, _external=True)})
        return redirect(url_for('index', path_name = parent(file_path)))
    else: abort(404)
    