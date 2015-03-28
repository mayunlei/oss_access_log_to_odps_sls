#!/usr/bin/env python
#encoding: utf-8

# Copyright (C) Alibaba Cloud Computing
# All rights reserved.

from slsresponse import SLSResponse
from histogram import Histogram

class GetHistogramsResponse(SLSResponse):
    """ The response of the GetHistograms API from sls.

    :type resp: dict
    :param resp: GetHistogramsResponse HTTP response body
    
    :type header: dict
    :param header: GetHistogramsResponse HTTP response header
    """
    
    def __init__(self, resp, header):
        SLSResponse.__init__(self, header)
        self.progress = resp['progress']
        self.count = resp['count']
        self.histograms = []
        for data in resp['histograms'] :
            status = Histogram(data['from'], data['to'], data['count'], data['progress'])
            self.histograms.append(status)
    
    def is_completed(self):
        """ Check if the histogram is completed
        
        :return: bool, true if this histogram is completed
        """
        return self.progress=='Complete'
    
    def get_total_count(self):
        """ Get total logs' count that current query hits
        
        :return: int, total logs' count that current query hits
        """
        return self.count
    
    def get_histograms(self):
        """ Get histograms on the requested time range: [from, to)
        
        :return: Histogram list, histograms on the requested time range: [from, to)
        """
        return self.histograms
    
    def sls_print(self):
        print 'GetHistogramsResponse:'
        print 'headers:', self.get_all_headers()
        print 'progress:', self.progress
        print 'count:', self.count
        print '\nhistograms class:\n'
        for data in self.histograms:
            data.sls_print()
            print
