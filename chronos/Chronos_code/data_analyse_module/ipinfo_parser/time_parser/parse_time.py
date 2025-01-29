#!/usr/bin/env python
# -*- encoding: utf-8 -*-
"""
@File    :   ipinfo.py
@Time    :   2021/12/30 23:59:59
@Author  :   gdd
@Version :   1.0
@Contact :   guyu@iie.ac.cn
@Desc    :
"""

import datetime
from .suffix_handle import modify
from .exceptions import AbnormalLMTFormat, AbnoramlLMTString, UnformatLMTString
from . import LMT_FORMAT_NORMAL, LMT_FORMAT_ABNORMAL


# 输入字符串，输出unix时间戳（整型）
def parse_time(lmt_string: str):
    # lmt字段过长，有可能是header提取错误
    # if len(lmt_string) > 100:
    if len(str(lmt_string)) > 100:
        raise AbnoramlLMTString("lmt字段过长，有可能是header提取错误：" + lmt_string[:100])

    # 本身就是unix时间戳
    if lmt_string.isdigit():
        lmt_int = int(lmt_string)  # 消除小数点的影响
        if len(str(lmt_int)) > 10:  # 判断是以毫秒为单位还是秒为单位
            lmt_int = lmt_int // 1000
        return lmt_int

    # 存在后缀的时候，先处理掉后缀
    # python从右往走找字符有两种方式，一种是rindex（没找着抛出异常），一种是rfind（没找着返回-1）
    lmt_string = modify(lmt_string)

    # 正式处理lmt字符串，格式化解析
    for format in LMT_FORMAT_NORMAL:
        lmt_object = try_transfer_datetime(lmt_string, format)
        if lmt_object is not None:
            return try_get_timestamp(lmt_object)

    # 没找到正常的lmt格式，继续判断是否为不正常的lmt
    for format in LMT_FORMAT_ABNORMAL:
        lmt_object = try_transfer_datetime(lmt_string, format)
        if lmt_object is not None:
            raise AbnormalLMTFormat("找到了错误的格式：" + lmt_string)

    # 如果执行到这里，那就是没有找到匹配的LMT格式了
    raise UnformatLMTString("没有找到匹配的LMT格式：" + lmt_string)


def try_get_timestamp(lmt_datetime):
    try:
        timestamp = lmt_datetime.timestamp()
        return int(timestamp)
    except OSError:
        return (lmt_datetime - datetime.datetime(1970, 1, 1)).total_seconds()
    except Exception as e:
        print("此种情况暂未处理，先捕获异常以保证程序能够完整运行", e)


def try_transfer_datetime(lm_string, format):
    try:
        result = datetime.datetime.strptime(lm_string, format)
    except ValueError:
        return None
    return result

#将时间戳转换成字符串
def parse_time_stamp(lmt_timestamp):
    try:
        return  datetime.datetime.fromtimestamp(lmt_timestamp).strftime("%Y-%m-%d %H:%M:%S")
    except OSError:
        return  datetime.datetime(1970, 1, 1) + datetime.timedelta(seconds= lmt_timestamp)
    except Exception:
        print("时间戳转字符串出错，数据条目为:", lmt_timestamp)
