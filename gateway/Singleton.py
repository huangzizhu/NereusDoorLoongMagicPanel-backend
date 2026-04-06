from abc import ABC, abstractmethod,ABCMeta
class SingletonMeta(ABCMeta):
    _instances = {}
    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            instance = super().__call__(*args, **kwargs)
            cls._instances[cls] = instance
        return cls._instances[cls]
def singletonInit(func):
    """装饰器：确保 __init__ 只执行一次"""
    def wrapper(self, *args, **kwargs):
        if not hasattr(self, '_inited'):
            func(self, *args, **kwargs)  # 执行子类 __init__ 逻辑
            self._inited = True
    return wrapper

class Singleton(metaclass=SingletonMeta):
    def __new__(cls, *args, **kwargs):
        return super().__new__(cls)

if __name__ == '__main__':
    # 子类 A
    class OrmEngineA(Singleton):
        @singletonInit
        def __init__(self, name: str):
            self.name = name
            print(f"Initializing {self.name}")


    # 子类 B
    class OrmEngineB(Singleton):
        @singletonInit
        def __init__(self):
            self.name = "OrmEngineB"
            print(f"Initializing {self.name}")


    # 创建并验证单例模式
    a1 = OrmEngineA("a1")
    a2 = OrmEngineA("a2")
    b1 = OrmEngineB()
    print(a1 is a2)  # True - OrmEngineA 的两个实例是相同的
    print(a1 is b1)  # False - OrmEngineA 和 OrmEngineB 是不同的单例
    print(a1.name, b1.name)  # "a1", "OrmEngineB"
    print(a1.name, a2.name)  # "a1", "a1"  重复初始化不会再次执行__init__