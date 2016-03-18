#  OSS Access log导入阿里云日志服务做分析

##功能

1：把OSS的access log 导入阿里云日志服务做查询。

2：通过阿里云日志服务对接下游各种实时消费系统比如jstorm或者odps做统计分析。

## 需要条件
+ 开通阿里云[日志服务](https://www.aliyun.com/product/sls) 

+ 使用SLS SDK需要安装protobuf和simplejson，具体见http://docs.aliyun.com/?spm=5176.383723.9.7.cMBsfX#/sls/sdk/python&quickstart



## 代码组成

+ SLS SDK ：http://docs.aliyun.com/?spm=5176.383723.9.7.DAjnRC#/sls/sdk/intros&overview

+ OSS SDK : http://docs.aliyun.com/?spm=5176.383663.9.4.RM0lJT#/oss/sdk/sdk-download&python

+ 核心代码在oss_tool.py


## 使用方法

### 必选参数
   1: --access_id  阿里云服务使用的access_id

   2: --access_key 阿里云服务使用的access_key

   oss相关参数：

   3：--oss_host:oss服务的地址，不同地区的bucket这个地址是不同的，请在bucket配置中获得这个参数。比如杭州地区的地址应该是：oss-cn-hangzhou.aliyuncs.com

   4: --log_store_bucket:access log保存的bucket名称

   5: --log_prefix：日志文件完整路径去掉之后的时间，前边的字符串，也是你在logging配置中的日志前缀+日志所代表的bucket名称。例如，bucket1的访问日志导入存放在bucket2中，并且在osslogging设置中的前缀为access_log_dir/xxxxx ，那么--log_prefix=access_log_dir/xxxxxbucket1  --log_store_bucket=bucket2

   6: --start_time: 表示从哪一刻开始导数据，比如2015-03-27
   
   7: --end_time : 表示导入日志的截至日期，不包含该日期，比如2016-03-18


   sls相关参数
   
   8：--sls_host:和oss_host类似，但是表示sls的地址，比如杭州集群是cn-hangzhou.sls.aliyun.com

   9: --sls_project： sls的project名称，是你在sls申请的，类似于bucket。

   10：--sls_logstore: sls的logsotre名称。表示把数据导入这个logstore.



### 可选参数：

   sls可选参数

   1: --sls_topic，表示导入到的topic名称，默认导入空的topic中

   2: --sls_quota:sls的quota，默认是1M/min，超过了这个值要手动调整这个quota，本脚本按照这个值指定的速度导数据，避免数据被SLS 拒绝。

 


### 一个例子
 
 ```
 python oss_tool.py  --access_id=id --access_key=key \
    --oss_host=oss.aliyuncs.com --log_prefix=access_log_dir/xxxxxbucket1 --log_store_bucket=bucket2 --start_time='2015-03-27' --end_time='2016-03-18'\
      --sls_host=cn-hangzhou.sls.aliyuncs.com   --sls_project=my_sls_project  --sls_logstore=oss_access_log --sls_quota=1
 ```

## 联系
  任何问题联系yunleisjtu+github@gmail.com
