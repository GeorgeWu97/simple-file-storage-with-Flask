# -*- coding:utf-8 -*-
from flask import Flask, render_template, abort, send_from_directory, request, redirect, url_for
from werkzeug.utils import secure_filename
import os
import json

validtype = ['txt', 'pdf', 'doc', 'docx', 'bmp', 'jpg', 'jpeg', 'png', 'gif', 'cr2',
             'ppt', 'pptx', 'pps', 'ppsx', 'avi', 'mov', 'qt', 'asf', 'rm', 'mp4',
             'mp3', 'wav', 'xls', 'xlsx', 'zip', 'rar', 'ico', 'icon']
def secure_path(path):
    item = path.strip().split('/')
    for name in item:
        if name == '..':
            return False
    return True
    
app = Flask('file_storage')

@app.route('/dir_index/<path:path_name>')
def index(path_name):
    if path_name[-1] == '/': path_name = path_name[:-1]
    def get_type(type):
        type = type.lower()[1:]
        if type in ['txt', 'pdf']: return type
        if type in ['doc', 'docx']: return 'word'
        if type in ['bmp', 'jpg', 'jpeg', 'png', 'gif', 'cr2', 'ico', 'icon']: return 'image'
        if type in ['ppt', 'pptx', 'pps', 'ppsx']: return 'ppt'
        if type in ['avi', 'mov', 'qt', 'asf', 'rm', 'mp4']: return 'video'
        if type in ['mp3', 'wav']: return 'music'
        if type in ['xls', 'xlsx']: return 'excel'
        return 'file'
        
    path = os.getcwd() + '/' + path_name    
    fd_list = os.listdir(path)
    index_list = []
    idx = 1
    for file in fd_list:
        if os.path.isfile(path + '/' + file):
            name, type = os.path.splitext(file)
            index_list.append([name, type[1:], get_type(type), idx])
        else:
            index_list.append([file, 'dir', 'folder', idx])
            
        idx += 1
   
    return render_template('index.html', list = index_list, path = path_name)

@app.route('/download/<path:file_path>')
def download(file_path):
    if not secure_path(file_path): abort(405)
    if file_path[-1]=='/': file_path = file_path[:-1]
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
    
if __name__ == '__main__':
    app.run(host = '127.0.0.1', port = '8080', debug = True)
    
