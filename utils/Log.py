def Log(func):
    # 给函数添加一个自定义属性
    setattr(func, "_enable_logging", True)
    return func