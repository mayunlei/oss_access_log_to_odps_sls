#!/usr/bin/env python
#coding=utf8
from optparse import OptionParser
import time
import re
from time import mktime
from aliyun.sls.slsclient import *
from aliyun.sls.logitem import *
from aliyun.sls.putlogsrequest import *
import hashlib
import os
import MySQLdb;
try:
    from oss.oss_api import *
except:
    from oss_api import *
try:
    from oss.oss_xml_handler import *
except:
    from oss_xml_handler import *
oss_access_id = ""
oss_access_key = ""
sls_access_id = ""
sls_access_key = ""
odps_access_id = ""
odps_access_key = ""
def getscriptdir():
    return os.path.split( os.path.realpath( __file__ ) )[0]
class OdpsHelper:
    def __init__(self,endpoint,tunnel_endpoint,access_id,access_key,project,table):
        self.endpoint = endpoint;
        self.tunnel_endpoint = tunnel_endpoint;
        self.access_id = access_id;
        self.access_key = access_key
        self.project = project
        self.table = table
        self.table_meta = [ "__time__","ip","time","http_method","url","status","send_bytes","request_time",  "referer",   "user_agent",  "oss_host","request_id", "aliyun_id",           "operation", "bucket",    "object","size","server_cost_time",           "error_code",   "bucket_owner_id"]
        odpscmd=getscriptdir()+"/odps/dship config --tunnel-endpoint="+tunnel_endpoint+" --endpoint="+endpoint+"  --id="+access_id+" --key="+ access_key+" --project="+project
        self.common_cmd = " -e "+ endpoint+" -te "+tunnel_endpoint+" -i "+access_id+" -k "+access_key +" "
        os.system(odpscmd);
        odpscmd='mkdir -p '+getscriptdir()+"/odps/conf"+';echo "access_id='+self.access_id+"\naccess_key="+self.access_key+"\nend_point="+self.endpoint+'\nproject_name='+self.project+'" > '+getscriptdir()+"/odps/conf/odps.conf";
        os.system(odpscmd);

    def createTable(self):
        sql = "create table "+self.table+"(inttime bigint,ip string,time string,http_method string, url string ,status bigint,send_bytes  bigint,request_time bigint,referer string,user_agent string,oss_host string ,request_id string,aliyun_id string,operation string,bucket_name string,object string,size string,server_cost_time string,error_code string,bucket_owner_id string) partitioned by (filename string);"
        print "execute this sql in odps console to create table";
        print sql
    def UploadToODPS(self,filename,logs):
        tmpfileName = "/tmp/sendtoodps-tmp-file"+filename;
        f=open(tmpfileName,'w')
        for log in logs:
            for key in self.table_meta:
                f.write(str(log[key]).replace(","," "));
                if key != self.table_meta[len(self.table_meta) -1] :
                    f.write(",")
            f.write("\n");
        f.close();
        createPartCmd = getscriptdir()+"/odps/bin/odps  sql \"ALTER TABLE oss_access_log  ADD IF NOT EXISTS PARTITION (filename='"+filename+"')\""
        os.system(createPartCmd)
        odpscmd=getscriptdir()+"/odps/dship upload "+self.common_cmd+tmpfileName+" "+self.project+"."+self.table+"/filename='"+filename+"'";
        os.system(odpscmd);
        os.remove(tmpfileName);
class MysqlHelper :
    def __init__(self,host,user,pwd,db,table):
        self.host = host;
        self.user = user;
        self.pwd = pwd;
        self.db = db;
        self.table = table;
        self.table_meta = [ "__time__","ip","time","http_method","url","status","send_bytes","request_time",  "referer",   "user_agent",  "oss_host","request_id", "aliyun_id",           "operation", "bucket",    "object","size","server_cost_time",           "error_code",   "bucket_owner_id"]
        self.intcols = ["inttime","status","send_bytes","request_time"];
    def UpdateToMysql(self,logs):
        sql = "insert into oss_logs (";
        for key in self.table_meta:
            sql += key
            if key != self.table_meta[len(self.table_meta) -1] :
                sql +=","
        sql+=") values";
        basesql =sql;
        conn = MySQLdb.connect(self.host,self.user,self.pwd,self.db );
        cursor = conn.cursor()
        for log in logs:
            sql = basesql;
            sql+="(";
            for key in self.table_meta:
                if key not in self.intcols:
                    sql +="'";
                sql += str(log[key]).replace("'","")
                if key not in self.intcols:
                    sql +="'";
                if key != self.table_meta[len(self.table_meta) -1] :
                    sql +=",";
            sql+=")";
            print sql;
            cursor.execute(sql);
        conn.commit()
        cursor.close();
        conn.close();

class OssHelper:
    def __init__(self,host,access_id,access_key):
        self.access_id = access_id
        self.access_key = access_key
        self.oss = OssAPI(host,access_id,access_key)
        self.pattern = []
        self.keys = []
        self.pattern.append(re.compile("\s+([\d\.]+)\s+\S+\s+\S+\s+\[(\S+)\s+\+\d+\]\s+\"(\S+)\s+(\S+)\s+\S+\"\s+(\d+)\s+(\d+)\s+(\d+)\s+\"(\S+)\"\s+\"([^\"]+)\"\s+\"(\S+)\"\s+\"(\S+)\"\s+\"(\S+)\"\s+\"\S+\"\s+\"(\S+)\"\s+\"(\S+)\"\s+\"(\S+)\"\s+(\S+)\s+(\S+)\s+\"\S+\"\s+(\d+)\s+\"(\d+)\".*"))
        self.pattern.append(re.compile("([\d\.]+)\s+(\d+)\s+\S+\s+\[(\S+)\s+\+\d+\]\s+\"(\S+)\s+(\S+)\s+\S+\"\s+(\d+)\s+(\d+)\s+(\d+)\s+\"(\S+)\"\s+\"([^\"]+)\"\s+\"(\S+)\"\s+\"(\S+)\"\s+\"\S+\"\s+\"\S+\"\s+\"(\S+)\"\s+\"(\S+)\"\s+\"(\S+)\"\s+(\d+)\s+(\d+)\s+\"\S+\"\s+(\d+)\s+\"(\d+)\"\s\S+\s+\"\S+\"\s+\"(\S+)\""))
        self.keys.append((                   "ip",                    "time",           "http_method","url",   "status","send_bytes",  "request_time",  "referer",   "user_agent",  "oss_host","request_id", "aliyun_id",           "operation", "bucket",    "object","size","server_cost_time",           "error_code",   "bucket_owner_id"))
        self.keys.append(("ip","key1","time","http_method","url","status","key2","key3","referer","user_agent","oss_host","request_id","oss_method","bucket","object","size","key4","key5","key6","oss_server_name"))
    def ListFile(self,bucket, prefix,beginStr):
        #列出bucket中所拥有的object
        marker = prefix+beginStr
        delimiter = ""
        maxkeys = "1000"
        headers = {}
        r = []
        while True:
            res = self.oss.get_bucket(bucket, prefix, marker, delimiter, maxkeys, headers)
            object = ""
            if (res.status / 100) == 2:
                body = res.read()
                h = GetBucketXml(body)
                (file_list, common_list) = h.list()
                if len(file_list) == 0:
                    break;
                for i in file_list:
                    r.append(i[0])
                marker = file_list[len(file_list) -1][0]
            else:
                print "get bucket error", res.status
                break;
        return r
    def ParseLog(self,log):
        for i in range(len(self.pattern)):
            m = self.pattern[i].match(log);
            if m is None:
                continue;
            if len(m.groups()) != len(self.keys[i]):
                print "keys not match,values are",m.groups(),
                return None
            r = {}
            for j in range(len(m.groups())):
                r[self.keys[i][j]]=m.groups()[j]
            t = time.strptime(r["time"],"%d/%b/%Y:%H:%M:%S")
            r["__time__"] = int(mktime(t))
            return r
        return None
    def GetFileContentAsLogs(self,bucket,path):
        headers = {}
        res = self.oss.get_object(bucket, path, headers)
        get_buffer_size = 10*1024*1024
        last = ""
        logs = []
        if(res.status /100) == 2:
            while True:
                content = res.read(get_buffer_size)
                if content:
                    final_content  = last+content
                    pos = 0;
                    while True:
                        if pos >= len(final_content) :
                            break;
                        end = final_content.find("\n",pos);
                        if end == -1:
                            last = final_content[pos,len(final_content)]
                            break
                        item = final_content[pos:end]
                        log = self.ParseLog(item)
                        if log is not None:
                            logs.append(log)
                        else:
                            print "error line",item
                        pos = end +1
                else:
                    break
        return logs
    
class SlsHelper :
    def __init__(self,host,access_id,access_key,project,logstore,topic,quota):
        self.host = host
        self.access_id = access_id
        self.access_key = access_key
        self.sls_client = SLSClient(host,self.access_id,self.access_key)
        self.project = project;
        self.logstore = logstore
        self.topic=topic 
        self.quota = quota*1024*1024
        self.startTime =  time.time();
        self.usedQuota = 0
        if topic  is None:
            self.topic = "";
    def SendLogs(self,logs):
        if logs is None:
            return
        for i in range(len(logs)/1024 + 1):
            endRange = (i+1)*1024
            if endRange > len(logs):
                endRange = len(logs)
            items=[]
            for j in range(i*2014,endRange):
                if logs[j] is None:
                        break;
                item = LogItem(logs[j]["__time__"])
                for key in logs[j]:
                    if key != "__time__":
                        item.push_back(key,logs[j][key])
                items.append(item)
            req = PutLogsRequest(self.project,self.logstore,self.topic,"",items)
            now = time.time();
            curSize = sys.getsizeof(req)
            if now - self.startTime > 60:
                self.usedQuota = curSize;
                self.startTime = now;
            else:
                if self.usedQuota + curSize > self.quota :
                    #print "sleep ",60-(now - self.startTime),"used quota",self.usedQuota,"cur size:",curSize
                    time.sleep(60-(now - self.startTime));
                    self.usedQuota = curSize;
                else:
                    self.usedQuota = self.usedQuota + curSize
            self.sls_client.put_logs(req)


if __name__ == "__main__": 
    parser = OptionParser()
    # options
    parser.add_option("", "--oss_access_id", dest="oss_access_id", help="oss access id,if not specified ,whill use access_id")
    parser.add_option("", "--oss_access_key", dest="oss_access_key", help="oss access key,if not specified ,whill use access_key")
    parser.add_option("", "--odps_access_id", dest="odps_access_id", help="odps access id,if not specified ,whill use access_id")
    parser.add_option("", "--odps_access_key", dest="odps_access_key", help="odps access key,if not specified ,whill use access_key")
    parser.add_option("", "--sls_access_id", dest="sls_access_id", help="sls access id,if not specified ,whill use access_id")
    parser.add_option("", "--sls_access_key", dest="sls_access_key", help="sls access key,if not specified ,whill use access_key")
    parser.add_option("", "--access_id", dest="access_id", help="access id,if not specified ,whill use access_id")
    parser.add_option("", "--access_key", dest="access_key", help="access key,if not specified ,whill use access_key")
    parser.add_option("", "--start_time", dest = "start_time",help="start time to download access_log")
    parser.add_option("", "--log_prefix", dest="log_prefix",help="if you store bucket1's access log in bucket2, and set prefix as prefix_path then the log path may like oss://${bucket2}/${prefix_path}${bucket1}_access_log_2014-12-30-13-00-00-0001, you should set --log_prefix=${prefix_path}${bucket1} and --log_store_bucket=${bucket2}")
    parser.add_option("", "--log_store_bucket",dest="log_store_bucket",help="if you store bucket1's access log in bucket2, and set prefix as prefix_path then the log path may like oss://${bucket2}/${prefix_path}${bucket1}_access_log_2014-12-30-13-00-00-0001, you should set --log_prefix=${prefix_path}${bucket1} and --log_store_bucket=${bucket2}")
    parser.add_option("","--to_sls" ,dest="send_log_to_sls",help=" if --to_sls is set in CLI ,log will send to sls",action="store_true")
    parser.add_option("","--to_odps" ,dest="send_log_to_odps",help="if --to_odps  is set in CLI,log will send to odps",action="store_true")
    parser.add_option("","--to_mysql" ,dest="send_log_to_mysql",help="if --to_mysql is set in CLI,log will send to odps",action="store_true")

    parser.add_option("","--oss_host",dest="oss_host",help="oss host name,e.g --oss_host=oss.aliyuncs.com or --oss_host=oss-cn-hangzhou.aliyuncs.com")
    parser.add_option("","--sls_host",dest="sls_host",help="sls host name,e.g --sls_host=sls-cn-hangzhou.aliyuncs.com")
    parser.add_option("","--sls_project",dest="sls_project",help="sls project  name,e.g --sls_project=xinhua_project")
    parser.add_option("","--sls_logstore",dest="sls_logstore",help="sls logstore name,e.g --sls_logstore=oss_access_log")
    parser.add_option("","--sls_topic",dest="sls_topic",help="sls logstore name,e.g --sls_topic=huabei")
    parser.add_option("","--sls_quota",dest="sls_quota",help="sls quota MB per minute,e.g.10M/minutes means --sls_quota=10",default="10",type="float");

    parser.add_option("","--odps_project",dest = "odps_project",help="odps project name");
    parser.add_option("","--odps_endpoint",dest="odps_endpoint",help="odps endpoint",default='http://service.odps.aliyun.com/api');
    parser.add_option("","--odps_tunnel_endpoing",dest="odps_tunnel_endpoint",help="odps tunnel endpoint",default='http://dt.odps.aliyun.com')
    parser.add_option("","--odps_table",dest="odps_table",help="odps table,default is :oss_access_log",default='oss_access_log')

    parser.add_option("","--db_host",dest="db_host",help="mysql db host",default="localhost");
    parser.add_option("","--db_user",dest="db_user",help="mysql db user",default="");
    parser.add_option("","--db_password",dest="db_password",help="mysql db password",default="");
    parser.add_option("","--db_database",dest="db_database",help="mysql db database",default="");
    parser.add_option("","--db_table",dest="db_table",help="mysql db table",default="");
    (option, args) = parser.parse_args()
    if option.access_id is not None  or  option.access_key is not None :
        oss_access_id = sls_access_id = odps_access_id = option.access_id
        oss_access_key = sls_access_key = odps_access_key = option.access_key
    else :
        oss_access_id = option.oss_access_id
        oss_access_key = option.oss_access_key
        sls_access_id = option.sls_access_id
        sls_access_key = option.sls_access_key
        odps_access_id = option.odps_access_id
        odps_access_key = option.odps_access_key

    if option.send_log_to_sls is None and option.send_log_to_odps is None and option.send_log_to_mysql is None:
        print "what do you want? send access log to sls or to odps or to mysql to all? please use --to_sls or --to_odps to specify. if you want to send to all,please set both flag"
        exit(0)
    if oss_access_id is None :
        print "Oss AccessId is not set,use --access_id=${} or --oss_access_id]${}"
        exit(0)
    if oss_access_key is None:
        print "Oss AccessKey is not set,use --access_key=${} or --oss_access_key]${}"
        exit(0)
    if option.oss_host is None:
        print "Oss Host is not set, e.g. --oss_host=oss.aliyuncs.com"
        exit(0)
    if option.log_prefix is None:
        print "--log_prefix must be set, it is at least the bucket name of the logging"
        exit(0)
    if option.log_store_bucket is None:
        print "--log_store_bucket must be set,it is the bucket name that store the log file "
        exit(0)
    if option.send_log_to_sls is not None:
        if option.sls_project is None :
            print "you have choose to send data to sls, --sls_project must be set"
            exit(0)
        if option.sls_logstore is None:
            print "you have choose to send data to sls, --sls_logstore must be set"
            exit(0)
        if option.sls_host is None :
            print "you have choose to send data to sls, --sls_host must be set"
            exit(0)
        if sls_access_id is None:
            print "you have choose to send data to sls, sls access id must be set, use --access_id or --sls_access_id"
            exit(0)
        if sls_access_key is None:
            print "you have choose to send data to sls, sls access key must be set, use --access_key or --sls_access_key"
            exit(0)

    if  option.send_log_to_odps is not None:
        if odps_access_id is None:
            print "you have choose to send data to odps, odps access id must be set, use --access_id or --odps_access_id"
            exit(0)
        if odps_access_key is None:
            print "you have choose to send data to odps, odps access key must be set, use --access_key or --odps_access_key"
            exit(0)
        if option.odps_project is None:
            print "you have choose to send data to odps , odps project must be set, use --odps_project"
            exit(0)
        if option.odps_endpoint is None:
            print "you have choose to send data to odps , odps project must be set, use --odps_endpoint"
            exit(0)
        if option.odps_tunnel_endpoint is None:
            print "you have choose to send data to odps , odps project must be set, use --odps_tunnel_endpoint"
            exit(0)

    if option.send_log_to_mysql is not None:
        if option.db_host is None:
            print "you have choose send data to mysql ,db_host must be set,use --db_host=";
            exit(0);
        if option.db_user is None:
            print "you have choose send data to mysql ,db_user must be set,use --db_user=";
            exit(0);
        if option.db_password is None:
            print "you have choose send data to mysql ,db_password must be set,use --db_password=";
            exit(0);
        if option.db_database is None:
            print "you have choose send data to mysql ,db_database  must be set,use --db_database=";
            exit(0);
        if option.db_table is None:
            print "you have choose send data to mysql ,db_table  must be set,use --db_table=";
            exit(0);

    beginStr = option.start_time
    if beginStr is None:
        beginStr = ""
    ossObj = OssHelper(option.oss_host,oss_access_id,oss_access_key)
    slsObj = None
    odpsObj = None
    if option.send_log_to_sls is not None:
        slsObj = SlsHelper(option.sls_host,sls_access_id,sls_access_key,option.sls_project,option.sls_logstore,option.sls_topic,option.sls_quota)
    if option.send_log_to_odps is not None:
        odpsObj = OdpsHelper(option.odps_endpoint,option.odps_tunnel_endpoint,odps_access_id,odps_access_key,option.odps_project,option.odps_table);
        odpsObj.createTable();
    if option.send_log_to_mysql is not None:
        mysqlObj =  MysqlHelper(option.db_host,option.db_user,option.db_password,option.db_database,option.db_table);
    files = ossObj.ListFile(option.log_store_bucket,option.log_prefix,beginStr);
    if len(files) == 0:
        print "no access log file found in oss://"+option.log_store_bucket+"/"+option.log_prefix
    for fIndex in range(len(files)):
        print files[fIndex],
        logs = ossObj.GetFileContentAsLogs(option.log_store_bucket,files[fIndex])
        if option.send_log_to_sls is not None:
            print "----> sls ",option.sls_project,"(",option.sls_logstore,")",len(logs)," records"
            slsObj.SendLogs(logs)
        if option.send_log_to_odps is not None:
            print "----> odps",option.odps_project,"(",option.odps_table,")",len(logs),"records"
            fileName = files[fIndex];
            odpsObj.UploadToODPS(fileName[len(option.log_prefix):len(fileName)],logs);
        if option.send_log_to_mysql is not None:
            print "----> to mysql "
            mysqlObj.UpdateToMysql(logs);


