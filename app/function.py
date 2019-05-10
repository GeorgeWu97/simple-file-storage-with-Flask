from flask import abort
from os import path, getcwd, mkdir, rmdir, remove, replace, listdir
import time as t

validtype = ['txt', 'pdf', 'doc', 'docx', 'bmp', 'jpg', 'jpeg', 'png', 'gif', 'cr2',
             'ppt', 'pptx', 'pps', 'ppsx', 'avi', 'mov', 'qt', 'asf', 'rm', 'mp4', 'mkv',
             'mp3', 'wav', 'xls', 'xlsx', 'zip', 'rar', '7z', 'iso', 'gz', 'z', 
             'ico', 'icon', 'html', 'css', 'js', 'py', 'c', 'cpp' ,'java']
def get_type(type):
    type = type.lower()[1:]
    if type in ['txt', 'pdf', 'iso']: return type
    if type in ['doc', 'docx']: return 'word'
    if type in ['bmp', 'jpg', 'jpeg', 'png', 'gif', 'cr2', 'ico', 'icon']: return 'image'
    if type in ['ppt', 'pptx', 'pps', 'ppsx']: return 'ppt'
    if type in ['avi', 'mov', 'qt', 'asf', 'rm', 'mp4', 'mkv']: return 'video'
    if type in ['mp3', 'wav']: return 'music'
    if type in ['xls', 'xlsx']: return 'excel'
    if type in ['zip', 'rar', '7z', 'gz', 'z']: return 'compression'
    return 'file'
    
def secure_path(path):
    return (path.find('..') == -1)

    
def normalsize(s):
    nexts = {'B':'K', 'K':'M', 'M':'G', 'G':'T'}
    ns = 'B'
    while s >=1024:
        s /= 1024
        ns = nexts[ns]
            
    return "%.4f"%s+ns
          
def dirsearch(dpath, cpath):
    if path.exists(dpath):
        index_list = []
        dsize = 0
        dtime = 0
        if path.isfile(dpath): abort(405)
        file_list = listdir(dpath)
        index_list = []
        idx = 1
        for file in file_list:
            ndpath = dpath+'/'+file
            ncpath = cpath+'/'+file
            if path.isfile(ndpath):
                try: 
                    size = path.getsize(ndpath)
                    time = path.getmtime(ndpath)
                    if time > dtime: dtime = time
                    dsize += size
                    size = normalsize(size)
                    if time == 0: time = '-------------------------'
                    else: time = TimeStampToTime(time)
                except OSError as err:
                    abort(405)
                    
                name, type = path.splitext(file)
                index_list.append([name, type[1:], get_type(type), idx, size, time])
            else:
                cl, size, time = dirsearch(ndpath, ncpath)
                dsize += size
                dtime += time
                if time > dtime: dtime = time
                dsize += size
                size = normalsize(size)
                if time == 0: time = '-------------------------'
                else: time = TimeStampToTime(time)
                index_list.append([file, 'dir', 'folder', idx, size, time])
            idx += 1
        return index_list, dsize, dtime    
    else: abort(405)
    
def TimeStampToTime(timestamp):
    timestruct = t.localtime(timestamp)
    return t.strftime('%Y-%m-%d %H:%M:%S',timestruct)    

def del_rec(str):
    if path.exists(str):
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

def valid_file(name):
    ext = name.rsplit('.',1)[1].lower()
    return (ext in validtype) and (name.find('\\')==-1 and name.find('/')==-1)
