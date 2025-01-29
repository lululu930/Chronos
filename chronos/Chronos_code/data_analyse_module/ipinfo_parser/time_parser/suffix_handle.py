import re

from data_analyse_module.ipinfo_parser.time_parser import LMT_FORMAT_ABNORMAL

SUFFIX_RE_FORMAT = [
    re.compile("\s+?[+|-]?0\d{2}0$"),
    re.compile("\s+?GMT.*$"),
    re.compile("\s+?[A-Z]{3,}$"),
    re.compile("\.\d{3}Z$")
]

CHINESE_DICT = {
    "一": "Mon",
    "二": "Tue",
    "三": "Wed",
    "四": "Thu",
    "五": "Fri",
    "六": "Sat",
    "日": "Sun",
    "10月": "Oct",
    "11月": "Nov",
    "12月": "Dec",
    "1月": "Jan",
    "2月": "Feb",
    "3月": "Mar",
    "4月": "Apr",
    "5月": "May",
    "6月": "Jun",
    "7月": "Jul",
    "8月": "Aug",
    "9月": "Sep",
    "Dez": "Dec"
}


def modify(lmt_string: str):
    for pattern in SUFFIX_RE_FORMAT:
        lmt_string = pattern.sub("", lmt_string)
    for key, value in CHINESE_DICT.items():
        lmt_string = lmt_string.replace(key, value)
    return lmt_string
