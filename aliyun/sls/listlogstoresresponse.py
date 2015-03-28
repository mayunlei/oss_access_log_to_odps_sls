#!/usr/bin/env python
#encoding: utf-8

# Copyright (C) Alibaba Cloud Computing
# All rights reserved.

from slsresponse import SLSResponse

class ListLogstoresResponse(SLSResponse):
    """ The response of the ListLogstores API from sls.
    
    :type resp: dict
    :param resp: ListLogstoresResponse HTTP response body
    
    :type header: dict
    :param header: ListLogstoresResponse HTTP response header
    """
    
    def __init__(self, resp, header):
        SLSResponse.__init__(self, header)
        self.count = resp['count']
        self.logstores = resp['logstores']

    def get_count(self):
        """ Get total count of logstores from the response
        
        :return: int, the number of total logstores from the response
        """
        return self.count
    
    def get_logstores(self):
        """ Get all the logstores from the response
        
        :return: list, all logstores
        """
        return self.logstores
    
    def sls_print(self):
        print 'ListLogstoresResponse:'
        print 'headers:', self.get_all_headers()
        print 'count:', self.count
        print 'logstores:', self.logstores
    
