# 该模块用于处理LMT字符串
# 输入：lmt字符串               一, 18  1月 2021 03:15:55
# 输出：python datetime对象    datetime()


LMT_FORMAT_NORMAL = [
    "%a, %d %B %Y %H:%M:%S",
    "%H:%M:%S, %d %b %Y",
    "%a %b %d %Y %H:%M:%S",
    "%a, %d %b %Y %H:%M:%S",
    "%a %b %d %H:%M:%S %Y",
    "%d %b %Y %H:%M:%S",
    "%a, %d %b %Y %H:%M:%S %p",
    "%a, %b %d %H:%M:%S %Y",
    "%A, %d %b %Y %H:%M:%S",
    "%a, %d %b %Y %H:%M:%S",
    "%a, %d %b %Y %H:%M:%SGMT",
    "%b, %d %Y %H:%M:%S",
    "%a, %b %d %Y %H:%M:%S",
    "%a %d %b %Y %H:%M:%S",
    "%A, %d-%b-%y %H:%M:%S",
    "%Y-%m-%d %H:%M:%S",
    "%A, %d-%b-%Y %H:%M:%S",
    "%Y-%m-%dT%H:%M:%S",

]

LMT_FORMAT_ABNORMAL = [
    "%A, %d",
    "%a, %d %b %Y",
    "%a, %y ws_notfound.html    0 00:00:00"
]
