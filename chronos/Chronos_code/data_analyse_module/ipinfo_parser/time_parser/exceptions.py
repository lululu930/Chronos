
# 非正常LMT格式异常类
class AbnormalLMTFormat(Exception):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)

# LMT字符串异常
class AbnoramlLMTString(Exception):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)

# 无法匹配的lmt字符串
class UnformatLMTString(Exception):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)
