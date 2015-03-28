#!/usr/bin/env python
#encoding: utf-8

# Copyright (C) Alibaba Cloud Computing
# All rights reserved.

from slsresponse import SLSResponse

class PutLogsResponse(SLSResponse):
    """ The response of the PutLogs API from sls.
    
    :type header: dict
    :param header: PutLogsResponse HTTP response header
    """
    
    def __init__(self, header):
        SLSResponse.__init__(self, header)
    
    def sls_print(self):
        print 'PutLogsResponse:'
        print 'headers:', self.get_all_headers()
