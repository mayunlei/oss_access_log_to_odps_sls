#!/usr/bin/env python
#encoding: utf-8

import re
import hmac
import zlib
import base64
import urllib
import socket
import hashlib

class Util:
    
    @staticmethod
    def is_row_ip(ip):
        iparray = ip.split('.')
        if len(iparray)!=4:
            return False
        for tmp in iparray:
            if not tmp.isdigit() or int(tmp)>=256:
                return False
        pattern = re.compile(r'^[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}$')
        if pattern.match(ip):
            return True
        return False
    
    @staticmethod
    def get_host_ip(slsHost):
        """ If it is not match your local ip, you should fill the PutLogsRequest
        parameter source by yourself.
        """
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect((slsHost, 80))
            ip = s.getsockname()[0]
            return ip
        except:
            return '127.0.0.1'
        finally:
            s.close()
    
    @staticmethod
    def compress_data(data):
        return zlib.compress(data,6)
    
    @staticmethod
    def cal_md5(content):
        return hashlib.md5(content).hexdigest().upper()

    @staticmethod
    def hmac_sha1(content, key):
        hashed = hmac.new(key, content, hashlib.sha1).digest()
        return base64.encodestring(hashed).rstrip()

    @staticmethod
    def url_encode_value(value):
        return urllib.quote(value)
    
    @staticmethod
    def url_encode(params):
        url = ''
        for key in sorted(params.iterkeys()):
            val = Util.url_encode_value(str(params[key]))
            url += key+'='+val+'&'
        return url[:-1] # strip the last &
    
    @staticmethod
    def canonicalized_sls_headers(headers):
        content = ''
        for key in sorted(headers.iterkeys()):
            if key[:6]=='x-sls-':  # x-sls- header
                content += key+':'+str(headers[key])+"\n";
        return content
    
    @staticmethod
    def canonicalized_resource(resource, params):
        if params:
            urlString = ''
            for key in sorted(params.iterkeys()):
                urlString += key+'='+str(params[key])+'&'
            return resource+'?'+urlString[:-1] # strip the last &
        return resource
    
    @staticmethod
    def get_request_authorization(method, resource, key, params, headers):
        if not key:
            return ''
        content = method+"\n"
        if 'Content-MD5' in headers:
            content += headers['Content-MD5']
        content += '\n'
        if 'Content-Type' in headers:
            content += headers['Content-Type']
        content += "\n"
        content += headers['Date']+"\n"
        content += Util.canonicalized_sls_headers(headers)
        content += Util.canonicalized_resource(resource, params)
        return Util.hmac_sha1(content, key)
    
