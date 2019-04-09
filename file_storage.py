#!/usr/bin/env python3

from hashlib import sha256
from re import match
from os import path, getcwd, mkdir, rmdir, remove, replace, listdir
from datetime import datetime
from collections import namedtuple
from tempfile import NamedTemporaryFile
from http.server import HTTPServer, BaseHTTPRequestHandler
from socketserver import ThreadingMixIn


ResponseStatus = namedtuple('HTTPStatus', 'code message')

ResponseData = namedtuple('ResponseData', 'status content_type '
                                          'content_length data_stream')
# set default values for 'content_type', 'content_length', 'data_stream'
ResponseData.__new__.__defaults__ = (None, None, None)

HTTP_STATUS = {"OK": ResponseStatus(code=200, message="OK"),
               "CREATED": ResponseStatus(code=201, message="Created"),
               "BAD_REQUEST": ResponseStatus(code=400, message="Bad request"),
               "NOT_FOUND": ResponseStatus(code=404, message="Not found"),
               "INTERNAL_SERVER_ERROR":
                   ResponseStatus(code=500, message="Internal server error")}

# buffer size that is used to hash, read, write files
CHUNK_SIZE = 256 * 1024
# path of directory where files are stored which is the current dir path of the Server
Root_DIR = getcwd() 
SERVER_ADDRESS = ('10.128.206.151', 6174)


def main():
    print('Http server is starting...')
    httpd = ThreadingServer(SERVER_ADDRESS, RequestsHandler)
    print('Http server is running...')
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    httpd.server_close()
    print('Http server closes...')


def sha256_hash_hex(file):
    """read file by chunks and return hash sha256"""
    data_hash = sha256()
    if file.seekable():
        file.seek(0)
    while True:
        copied_bytes = file.read(CHUNK_SIZE)
        data_hash.update(copied_bytes)
        if len(copied_bytes) < CHUNK_SIZE:
            break
    return data_hash.hexdigest()


def date_now():
    return datetime.now().strftime('[%d/%b/%Y %H:%M:%S]')


def copyfile(in_stream, out_stream):
    """Copy data from in_stream to  out_stream by chunks."""

    while True:
        copied_bytes = in_stream.read(CHUNK_SIZE)
        out_stream.write(copied_bytes)
        if len(copied_bytes) < CHUNK_SIZE:
            break


class ThreadingServer(ThreadingMixIn, HTTPServer):
    """An HTTP Server that handle each request in a new thread"""

    daemon_threads = True


class HTTPStatusError(Exception):
    """Exception wrapping a value from http.server.HTTPStatus"""

    def __init__(self, status, description=None):
        """
        Constructs an error instance from a tuple of
        (code, message, description), see http.server.HTTPStatus
        """
        # super(HTTPStatusError, self).__init__()
        # self.code = status.code
        # self.message = status.message
        # self.explain = description
        self.code = status.code
        self.message = status.message
        self.explain = description


class RequestsHandler(BaseHTTPRequestHandler):
    """
    Simple HTTP request handler with GET/DELETE/POST commands
    This class implements API.
    Base url API: /v1/files/
    The name and the unique identifier of a file is the value of
    MD5 hash function where the function argument is a file. It looks like
    a string which consists of hexadecimal digits.
    """

    def do_POST(self):
        """Handles GET-requests by url /v1/files/[md5_hash]
        Returns a file if it exists
        """
        
        url_path = self.path.rstrip()

        print("{0}\t[START]: Received POST for {1}".format(date_now(),
                                                           url_path))

        try:
            if match(r'^/share/?', url_path):
                response = self.upload_file()
                self.send_headers(response.status, response.content_type,
                                  response.content_length)
                if response.data_stream:
                    self.wfile.write(response.data_stream)

            else:
                self.handle_not_found()
        except HTTPStatusError as err:
            self.send_error(err.code, err.message, err.explain)
        print("{}\t[END]".format(date_now()))

    def do_GET(self):
        """Handles GET-requests by url /v1/files/[md5_hash]
        Returns a file if it exists
        """

        url_path = self.path.rstrip()

        print("{0}[START]: Received GET for {1}".format(date_now(),
                                                          url_path))

        try:
            if match(r'^/share/?', url_path):
                response = self.download_file()
                self.send_headers(response.status, response.content_type,
                                  response.content_length)
                if response.data_stream:
                    try:
                        copyfile(response.data_stream, self.wfile)
                    except OSError as err:
                        raise HTTPStatusError(
                            HTTP_STATUS["INTERNAL_SERVER_ERROR"], str(err))
                    finally:
                        if response.data_stream is not None:
                            response.data_stream.close()
            else:
                self.handle_not_found()
        except HTTPStatusError as err:
            self.send_error(err.code, err.message, err.explain)

        print("{}\t[END]".format(date_now()))

    def do_DELETE(self):
        """Handles DELETE-requests by url /v1/files/[md5_hash]
        Deletes a file if it exists
        """

        url_path = self.path.rstrip()

        print("{0}\t[START]: Received DELETE for {1}".format(date_now(),
                                                             url_path))

        try:
            if match(r'^/share/?', url_path):
                response = self.delete_file()
                self.send_headers(response.status)
            else:
                self.handle_not_found()
        except HTTPStatusError as err:
            self.send_error(err.code, err.message, err.explain)

        print("{}[END]".format(date_now()))

    def handle_not_found(self):
        """Handles routing for unexpected paths"""
        raise HTTPStatusError(HTTP_STATUS["NOT_FOUND"], "File not found")

    def send_headers(self, status, content_type=None, content_length=None):
        """Send out the group of headers for a successful request"""

        self.send_response(status.code, status.message)
        if content_type:
            self.send_header('Content-Type', content_type)
        if content_length:
            self.send_header('Content-Length', content_length)
        self.end_headers()

    def upload_file(self):
        """Upload file to server and return response data"""
        payload = None

        url_path = self.path.rstrip()
        url_dir = url_path.split('/')[1:]
        file_path = Root_DIR
        for item in url_dir: file_path += '/' + item 
        file_dir = file_path + '/'
        

        try:
            if "Content-Name" in self.headers:
                try:
                    content_name = self.headers['Content-Name']
                    file_path = file_dir + content_name
                except ValueError:
                    raise HTTPStatusError(HTTP_STATUS["BAD_REQUEST"],
                                          "Wrong parameters")
            # raise HTTPStatusError(HTTP_STATUS["BAD_REQUEST"],
            #                       "Wrong parameters")
            if not path.exists(file_dir):
                mkdir(file_dir)

            if 'Content-Length' in self.headers:
                try:
                    content_len = int(self.headers['Content-Length'])
                except ValueError:
                    raise HTTPStatusError(HTTP_STATUS["BAD_REQUEST"],
                                          "Wrong parameters")
                if content_len:

                    # create temp file which has constraint of buffer size
                    payload = NamedTemporaryFile(dir=file_dir,
                                                 buffering=CHUNK_SIZE,
                                                 delete=False)

                    # use rfile.read1() instead rfile.read() since
                    # rfile.read() allows to read only the exact
                    # number of bytes
                    while True:
                        copied_bytes = self.rfile.read1(CHUNK_SIZE)
                        payload.write(copied_bytes)
                        if len(copied_bytes) < CHUNK_SIZE:
                            break
                    payload.seek(0)

                    file_hash = sha256_hash_hex(payload)

                    # try:
                    #     mkdir(FILES_DIR)
                    # except FileExistsError as err:
                    #     print(err)

                    # file_dir = FILES_DIR + file_hash[:2] + '/'
                    # file_path = file_dir + file_hash

                    if not path.exists(file_path):
                        # try:
                        #     mkdir(file_dir)
                        # except FileExistsError as err:
                        #     print(err)

                        # protection against race condition
                        # replace temporary file with name file_path
                        tmp_file = payload.name
                        replace(tmp_file, file_path)

                        data = bytes(file_hash.encode('UTF-8'))
                        content_len = len(data)

                        return ResponseData(
                            status=HTTP_STATUS['CREATED'],
                            content_type='text/plain; charset=utf-8',
                            content_length=content_len, data_stream=data)

                    return ResponseData(status=HTTP_STATUS['OK'])

            # raise HTTPStatusError(HTTP_STATUS["BAD_REQUEST"],
            #                       "Wrong parameters")

        except OSError as err:
            raise HTTPStatusError(HTTP_STATUS["INTERNAL_SERVER_ERROR"],
                                  str(err))
        finally:
            if payload is not None:
                try:
                    remove(payload.name)
                except OSError as err:
                    if err.errno == 2:
                        pass
                    else:
                        raise HTTPStatusError(
                            HTTP_STATUS["INTERNAL_SERVER_ERROR"], str(err))

    def download_file(self):
        """If requested file exists return response data for downloading"""

        url_path = self.path.rstrip()
        url_dir = url_path.split('/')[1:]
        file_path = Root_DIR
        for item in url_dir: file_path += '/' + item 
        data_stream = None
        
        if path.exists(file_path):
            try:
                if path.isfile(file_path):
               
                    data_stream = open(file_path, 'br')
                    content_len = path.getsize(file_path)
                    return ResponseData(
                        status=HTTP_STATUS['OK'],
                        content_type='application/octet-stream',
                        content_length=content_len, data_stream=data_stream)
                else:
                    file_list = listdir(file_path)
                    with open(file_path + '/listdir.html', 'w', encoding = 'utf-8') as w:
                        for file in file_list: 
                            if file != 'listdir.html':
                                w.write(file + '<br/>')
                        w.close()
                    
                    data_stream = open(file_path + '/listdir.html', 'br')
                    content_len = path.getsize(file_path + '/listdir.html')
                    return ResponseData(status = HTTP_STATUS['OK'],
                                        content_type = 'text/html',
                                        data_stream = data_stream)
                                        
            except OSError as err:
                if data_stream is not None:
                    data_stream.close()
                raise HTTPStatusError(HTTP_STATUS["INTERNAL_SERVER_ERROR"],
                                      str(err))

        else:
            self.handle_not_found()

    def delete_file(self):
        """Delete file if exists"""

        url_path = self.path.rstrip()
        url_dir = url_path.split('/')[1:]
        file_path = Root_DIR
        for item in url_dir: file_path += '/' + item 
        
        if path.exists(file_path):
            try:
                self.del_rec(file_path)
                return ResponseData(status=HTTP_STATUS['OK'])
            except OSError as err:
                raise HTTPStatusError(HTTP_STATUS["INTERNAL_SERVER_ERROR"],
                                      str(err))
        else:
            self.handle_not_found()
            
    def del_rec(self, str):
        """Delete directories recursively"""
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
                        print(str1)
                        self.del_rec(str1)
                            
                    rmdir(str)
                except OSError as err:
                    print(err)

if __name__ == '__main__':
    main()
