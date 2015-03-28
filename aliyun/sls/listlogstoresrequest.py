#!/usr/bin/env python
#encoding: utf-8

# Copyright (C) Alibaba Cloud Computing
# All rights reserved.

from slsrequest import SLSRequest

class ListLogstoresRequest(SLSRequest):
    """ The request used to list log store from sls.
    
    :type project: string
    :param project: project name
    """
    
    def __init__(self, project=None):
        SLSRequest.__init__(self, project)
