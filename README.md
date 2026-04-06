# FastAPI Gateway 模板项目
基于 **FastAPI** 开发的标准化网关服务模板，遵循**Web三层架构**，集成全局异常处理、Token鉴权、ORM数据库操作、JWT令牌、日志系统、单例模式等核心能力，开箱即用，可直接作为企业级后端项目开发底座。

## ✨ 项目特性
- 🌐 **FastAPI 框架**：高性能异步Web框架，自动生成API文档
- 🏗️ **标准三层架构**：Controller(控制层) → Service(业务层) → Dao(数据访问层)
- 🛡️ **全局异常处理器**：统一捕获并格式化返回所有异常信息
- 🔐 **全局拦截器**：自动完成Token校验、接口访问日志记录
- 🎯 **单例模式**：统一管理Controller/Service/Dao实例，避免重复创建
- 🪪 **JWT令牌**：封装长短双Token机制，支持令牌过期、校验、刷新
- 📝 **日志系统**：装饰器式日志注解，支持全局/方法级日志打印
- 📦 **统一响应体**：标准化接口返回格式，前后端交互更规范
- 🗄️ **ORM数据库**：基于ORM引擎操作数据库，简化SQL编写
- 📌 **Python版本**：推荐 Python 3.10+

## 📁 项目结构
```
├── 📂 Exception          # 自定义异常集合
├── 📂 gateway            # 核心业务模块（三层架构）
│   ├── 📂 controller     # 控制层：接口路由定义
│   ├── 📂 dao            # 数据访问层：数据库操作
│   ├── 📂 orm            # ORM模型与数据库引擎
│   └── 📂 service        # 业务逻辑层
├── 📂 pojo               # 数据实体类
├── 📂 sql                # 数据库初始化脚本
├── 📂 utils              # 工具类：JWT、日志等
├── 📄 main.py            # 项目启动入口
├── 📄 requirements.txt   # 项目依赖清单
└── 📄 ProjectRoot.py     # 项目根路径配置
```

## 🚀 快速开始
### 1. 环境准备
```bash
# 推荐 Python 3.10+
python --version

# 安装依赖
pip install -r requirements.txt
```

### 2. 初始化数据库
执行 `sql/log.sql` 脚本创建数据库表  
默认使用 `panel.db` SQLite数据库，无需额外配置

### 3. 启动项目
```bash
python main.py
```

### 4. 访问API文档
- Swagger文档：http://127.0.0.1:8000/docs
- ReDoc文档：http://127.0.0.1:8000/redoc

## 🎯 核心模块使用说明
### 1. 统一响应格式
所有接口统一返回标准JSON格式，无需手动封装：
```python
from gateway.Response import Response

# 成功响应
return Response.success(data={"id": 1}, msg="操作成功")

# 失败响应
return Response.error(msg="操作失败")
```
**响应格式**
```json
{
  "code": 1,  // 1成功 0失败
  "msg": "success",
  "data": {}
}
```

### 2. 单例模式使用
Controller/Service/Dao 必须继承单例类，保证全局唯一实例：
```python
from gateway.Singleton import Singleton, singletonInit

class UserService(Singleton):
    @singletonInit  # 装饰初始化方法
    def __init__(self):
        self.user_dao = UserDao()  # 依赖其他单例
```

### 3. 全局异常处理
直接抛出自定义异常，全局处理器会自动捕获并返回：
```python
from Exception.UserNotFoundException import UserNotFoundException

# 抛出自定义异常
raise UserNotFoundException("用户不存在")
```

### 4. JWT令牌工具
生成/校验长短Token，支持令牌过期、权限校验：


### 5. 日志功能
使用装饰器记录方法执行日志：
```python
from utils.Log import Log

@Log  # 装饰需要打印日志的方法
def login(self, username: str, password: str):
    pass
```

### 6. 项目配置与路由注册
在 `gateway/app.py` 中统一配置项目、注册控制器：
```python
# 注册控制器
app.include_router(LogController.router)
```

## 📋 自定义异常列表
| 异常类 | 说明 |
|--------|------|
| DataBaseException | 数据库操作异常 |
| InvalidTokenException | 无效Token异常 |
| PasswordIncorrectException | 密码错误异常 |
| TokenAuthException | Token认证异常 |
| TokenExpiredException | Token过期异常 |
| UserNotFoundException | 用户不存在异常 |

## 🛠️ 技术栈
- **Web框架**：FastAPI
- **数据库**：SQLite（可替换MySQL/PostgreSQL）
- **ORM**：原生ORM封装
- **令牌认证**：PyJWT
- **异常处理**：全局异常捕获
- **设计模式**：单例模式、装饰器模式

## 📌 注意事项
1. 所有业务类必须继承 `Singleton` 并使用 `@singletonInit` 装饰`__init__`
2. 新增接口需在 `app.py` 中注册控制器路由
3. 拦截器Token校验默认开启，可根据需求调整
4. 日志功能默认开启，通过装饰器控制打印范围

---

## 📄 License
本项目为开源模板，仅供学习和项目开发使用

---

# 规范说明
- 代码遵循PEP8规范
- 类名使用大驼峰命名法
- 方法名/变量名使用小驼峰命名法
- 所有核心方法添加注释说明

---
