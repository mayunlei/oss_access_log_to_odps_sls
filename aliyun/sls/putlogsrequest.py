#!/usr/bin/env python
#encoding: utf-8

# Copyright (C) Alibaba Cloud Computing
# All rights reserved.

from slsrequest import SLSRequest

class PutLogsRequest(SLSRequest):
    """ The request used to send data to sls. 
    
    :type project: string
    :param project: project name
    
    :type logstore: string
    :param logstore: logstore name
    
    :type topic: string
    :param topic: topic name

    :type source: string
    :param source: source of the logs
    
    :type logitems: list<LogItem>
    :param logitems: log data
    """
    
    def __init__(self, project=None, logstore=None, topic=None, source=None, logitems=None):
        SLSRequest.__init__(self, project)
        self.logstore = logstore
        self.topic = topic
        self.source = source
        self.logitems = logitems

    def get_logstore(self):
        """ Get logstore name
        
        :return: string, logstore name
        """
        return self.logstore if self.logstore else ''
    
    def set_logstore(self, logstore):
        """ Set logstore name
        
        :type logstore: string
        :param logstore: logstore name
        """
        self.logstore = logstore
    
    
    def get_topic(self):
        """ Get topic name
        
        :return: string, topic name
        """
        return self.topic if self.topic else ''
    
    def set_topic(self, topic):
        """ Set topic name
        
        :type topic: string
        :param topic: topic name
        """
        self.topic = topic
    
    
    def get_source(self):
        """ Get log source
        
        :return: string, log source
        """
        return self.source
    
    def set_source(self, source):
        """ Set log source
        
        :type source: string
        :param source: log source
        """
        self.source = source
    
    
    def get_log_items(self):
        """ Get all the log data
        
        :return: LogItem list, log data
        """
        return self.logitems
    
    def set_log_items(self, logitems):
        """ Set the log data
        
        :type logitems: LogItem list
        :param logitems: log data
        """
        self.logitems = logitems

