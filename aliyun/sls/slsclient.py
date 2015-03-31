#!/usr/bin/env python
# encoding: utf-8

# Copyright (C) Alibaba Cloud Computing
# All rights reserved.

import sys
import httplib
try:
    import json
except ImportError:
    import simplejson as json
from datetime import datetime
from sls_logs_pb2 import LogGroup
from aliyun.sls.util import Util
from aliyun.sls.slsexception import SLSException
from aliyun.sls.getlogsresponse import GetLogsResponse
from aliyun.sls.putlogsresponse import PutLogsResponse
from aliyun.sls.listtopicsresponse import ListTopicsResponse
from aliyun.sls.listlogstoresresponse import ListLogstoresResponse
from aliyun.sls.gethistogramsresponse import GetHistogramsResponse

CONNECTION_TIME_OUT = 20
API_VERSION = '0.4.0'
USER_AGENT = 'yunlei-python-sdk-v-0.4.1'

"""
SlsClient class is the main class in the SDK. It can be used to communicate with 
SLS server to put/get data.

:Author: sls_dev
"""

class SLSClient(object):
    """ Construct the SLSClient with endpoint, accessKeyId, accessKey.
    
    :type endpoint: string
    :param endpoint: SLS host name, for example, http://ch-hangzhou.sls.aliyuncs.com
    
    :type accessKeyId: string
    :param accessKeyId: aliyun accessKeyId
    
    :type accessKey: string
    :param accessKey: aliyun accessKey
    """
    
    __version__ = API_VERSION
    Version = __version__
    
    def __init__(self, endpoint, accessKeyId, accessKey):
        self._isRowIp = True
        self._port = 80
        self._setendpoint(endpoint)
        self._accessKeyId = accessKeyId
        self._accessKey = accessKey
        self._timeout = CONNECTION_TIME_OUT
        self._source = Util.get_host_ip(self._slsHost)

    def _setendpoint(self, endpoint):
        pos = endpoint.find('://')
        if pos != -1:
            endpoint = endpoint[pos + 3:]  # strip http://
        pos = endpoint.find('/')
        if pos != -1:
            endpoint = endpoint[:pos]
        pos = endpoint.find(':')
        if pos != -1:
            self._port = int(endpoint[pos + 1:])
            endpoint = endpoint[:pos]
        self._isRowIp = Util.is_row_ip(endpoint)
        self._slsHost = endpoint
        self._endpoint = endpoint + ':' + str(self._port)

    def _getGMT(self):
        return datetime.utcnow().strftime('%a, %d %b %Y %H:%M:%S GMT')

    def _loadJson(self, respJson, requestId):
        if not respJson:
            return None
        try:
            return json.loads(respJson)
        except:
            raise SLSException('SLSBadResponse', 
                               'Bad json format:\n%s' % respJson,
                               requestId)
    
    def _getHttpResponse(self, method, url, body, headers):
        try:
            if sys.version_info >= (2, 6):
                self._con = httplib.HTTPConnection(self._slsConHost, self._port, self._timeout)
            else:
                httplib.socket.setdefaulttimeout(self._timeout)
                self._con = httplib.HTTPConnection(self._slsConHost, self._port)
        except Exception, ex:
            raise SLSException('SLSRequestError', str(ex))
        headers['User-Agent'] = USER_AGENT
        try:
            self._con.request(method, url, body, headers)
            hresp = self._con.getresponse()
            return (hresp.status, hresp.read(), hresp.getheaders())
        except SLSException, ex:
            raise ex
        except Exception, ex:
            raise SLSException('SLSRequestError', str(ex))
        finally:
            self._con.close()
    
    def _sendRequest(self, method, url, body, headers):
        (status, respJson, respHeader) = self._getHttpResponse(method, url, body, headers)
        header = {}
        if isinstance(respHeader, dict):
            header = respHeader
        else:
            for key, value in respHeader:
                header[key] = value
        
        requestId = header['x-sls-requestid'] if 'x-sls-requestid' in header else ''
        exJson = self._loadJson(respJson, requestId)
        
        if status == 200:
            return (exJson, header)
        elif 'error_code' in exJson and 'error_message' in exJson:
            raise SLSException(exJson['error_code'], exJson['error_message'], requestId)
        else:
            exJson = '. Return json is '+str(exJson) if exJson else '.'
            raise SLSException('SLSRequestError', 
                               'Request is failed. Http code is '+str(status)+exJson, requestId)
    
    def _send(self, method, project, body, resource, params, headers):
        if body:
            headers['Content-Length'] = len(body)
            headers['Content-MD5'] = Util.cal_md5(body)
            headers['Content-Type'] = 'application/x-protobuf'
        else:
            headers['Content-Length'] = 0
            headers["x-sls-bodyrawsize"] = 0
            headers['Content-Type'] = ''
        
        headers['x-sls-apiversion'] = API_VERSION
        headers['x-sls-signaturemethod'] = 'hmac-sha1'
        if self._isRowIp:
            self._slsConHost = self._slsHost
        else:
            self._slsConHost = project + "." + self._slsHost
        headers['Host'] = project + "." + self._slsHost
        headers['Date'] = self._getGMT()
        
        signature = Util.get_request_authorization(method, resource,
            self._accessKey, params, headers)
        headers['Authorization'] = "SLS " + self._accessKeyId + ':' + signature
        if params:
            resource += '?' + Util.url_encode(params)
        
        return self._sendRequest(method, resource, body, headers)
    
    
    def put_logs(self, request):
        """ Put logs to SLS.
        Unsuccessful opertaion will cause an SLSException.
        
        :type request: PutLogsRequest
        :param request: the PutLogs request parameters class
        
        :return: PutLogsResponse
        
        :raise: SLSException
        """
        if len(request.get_log_items()) > 4096:
            raise SLSException('InvalidLogSize', 
                            "logItems' length exceeds maximum limitation: 4096 lines.")
        logGroup = LogGroup()
        logGroup.Topic = request.get_topic()
        if request.get_source():
            logGroup.Source = request.get_source()
        else:
            if self._source=='127.0.0.1':
                self._source = Util.get_host_ip(request.get_project() + '.' + self._slsHost)
            logGroup.Source = self._source
        for logItem in request.get_log_items():
            log = logGroup.Logs.add()
            log.Time = logItem.get_time()
            contents = logItem.get_contents()
            for key, value in contents:
                content = log.Contents.add()
                content.Key = unicode(key, 'utf-8')
                content.Value = unicode(value, 'utf-8')
        body = logGroup.SerializeToString()
        if len(body) > 3 * 1024 * 1024:  # 3 MB
            raise SLSException('InvalidLogSize', 
                            "logItems' size exceeds maximum limitation: 3 MB.")
        
        headers = {}
        headers['x-sls-bodyrawsize'] = len(body)
        headers['x-sls-compresstype'] = 'deflate'
        body = Util.compress_data(body)
        params = {}
        logstore = request.get_logstore()
        project = request.get_project()
        resource = '/logstores/' + logstore
        respHeaders = self._send('POST', project, body, resource, params, headers)
        return PutLogsResponse(respHeaders[1])
    
    def list_logstores(self, request):
        """ List all logstores of requested project.
        Unsuccessful opertaion will cause an SLSException.
        
        :type request: ListLogstoresRequest
        :param request: the ListLogstores request parameters class.
        
        :return: ListLogStoresResponse
        
        :raise: SLSException
        """
        headers = {}
        params = {}
        resource = '/logstores'
        project = request.get_project()
        (resp, header) = self._send("GET", project, None, resource, params, headers)
        return ListLogstoresResponse(resp, header)
    
    def list_topics(self, request):
        """ List all topics in a logstore.
        Unsuccessful opertaion will cause an SLSException.
        
        :type request: ListTopicsRequest
        :param request: the ListTopics request parameters class.
        
        :return: ListTopicsResponse
        
        :raise: SLSException
        """
        headers = {}
        params = {}
        if request.get_token()!=None:
            params['token'] = request.get_token()
        if request.get_line()!=None:
            params['line'] = request.get_line()
        params['type'] = 'topic'
        logstore = request.get_logstore()
        project = request.get_project()
        resource = "/logstores/" + logstore
        (resp, header) = self._send("GET", project, None, resource, params, headers)
        return ListTopicsResponse(resp, header)

    def get_histograms(self, request):
        """ Get histograms of requested query from SLS.
        Unsuccessful opertaion will cause an SLSException.
        
        :type request: GetHistogramsRequest
        :param request: the GetHistograms request parameters class.
        
        :return: GetHistogramsResponse
        
        :raise: SLSException
        """
        headers = {}
        params = {}
        if request.get_topic()!=None:
            params['topic'] = request.get_topic()
        if request.get_from()!=None:
            params['from'] = request.get_from()
        if request.get_to()!=None:
            params['to'] = request.get_to()
        if request.get_query()!=None:
            params['query'] = request.get_query()
        params['type'] = 'histogram'
        logstore = request.get_logstore()
        project = request.get_project()
        resource = "/logstores/" + logstore
        (resp, header) = self._send("GET", project, None, resource, params, headers)
        return GetHistogramsResponse(resp, header)

    def get_logs(self, request):
        """ Get logs from SLS.
        Unsuccessful opertaion will cause an SLSException.
        
        :type request: GetLogsRequest
        :param request: the GetLogs request parameters class.
        
        :return: GetLogsResponse
        
        :raise: SLSException
        """
        headers = {}
        params = {}
        if request.get_topic()!=None:
            params['topic'] = request.get_topic()
        if request.get_from()!=None:
            params['from'] = request.get_from()
        if request.get_to()!=None:
            params['to'] = request.get_to()
        if request.get_query()!=None:
            params['query'] = request.get_query()
        params['type'] = 'log'
        if request.get_line()!=None:
            params['line'] = request.get_line()
        if request.get_offset()!=None:
            params['offset'] = request.get_offset()
        if request.get_reverse()!=None:
            params['reverse'] = 'true' if request.get_reverse() else 'false'
        logstore = request.get_logstore()
        project = request.get_project()
        resource = "/logstores/" + logstore
        (resp, header) = self._send("GET", project, None, resource, params, headers)
        return GetLogsResponse(resp, header)
    
