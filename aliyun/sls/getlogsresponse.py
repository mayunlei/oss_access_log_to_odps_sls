#!/usr/bin/env python
#encoding: utf-8

# Copyright (C) Alibaba Cloud Computing
# All rights reserved.

from slsresponse import SLSResponse
from queriedlog import QueriedLog

class GetLogsResponse(SLSResponse):
    """ The response of the GetLog API from sls.
    
    :type resp: dict
    :param resp: GetLogsResponse HTTP response body
    
    :type header: dict
    :param header: GetLogsResponse HTTP response header
    """
    
    def __init__(self, resp, header):
        SLSResponse.__init__(self, header)
        self.count = resp['count']
        self.progress = resp['progress']
        self.logs = []
        for data in resp['logs']:
            contents = {}
            for key in data.iterkeys():
                if key!='__time__' and key!='__source__':
                    contents[key] = data[key]
            self.logs.append(QueriedLog(data['__time__'], data['__source__'], contents))

    
    def get_count(self):
        """ Get log number from the response
        
        :return: int, log number
        """
        return self.count
    
    def is_completed(self):
        """ Check if the get logs query is completed
        
        :return: bool, true if this logs query is completed
        """
        return self.progress=='Complete'
    
    def get_logs(self):
        """ Get all logs from the response
        
        :return: QueriedLog list, all log data
        """
        return self.logs
    
    def sls_print(self):
        print 'GetLogsResponse:'
        print 'headers:', self.get_all_headers()
        print 'count:', self.count
        print 'progress:', self.progress
        print '\nQueriedLog class:\n'
        for log in self.logs:
            log.sls_print()
            print
