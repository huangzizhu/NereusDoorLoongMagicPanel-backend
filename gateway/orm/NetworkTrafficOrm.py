from sqlalchemy import Column, Integer, String, Float, DateTime, func
from gateway.orm.OrmEngine import OrmEngine




class NetworkTrafficOrm(OrmEngine().getBase()):
    """
    网卡流量监控 ORM 模型
    对应数据库表：network_traffic
    """
    __tablename__ = 'network_traffic'

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    interfaceName = Column('interface_name', String(50), nullable=False, comment="网卡名称")
    ipAddress = Column('ip_address', String(50), nullable=True, comment="IP地址")
    macAddress = Column('mac_address', String(50), nullable=True, comment="MAC地址")
    uploadSpeed = Column('upload_speed', Float, nullable=False, comment="上传速率")
    downloadSpeed = Column('download_speed', Float, nullable=False, comment="下载速率")
    uploadTotal = Column('upload_total', Integer, nullable=True, comment="累计上传流量")
    downloadTotal = Column('download_total', Integer, nullable=True, comment="累计下载流量")
    status = Column(Integer, default=1, comment="网卡状态：0-禁用, 1-启用")
    createTime = Column('create_time', DateTime, server_default=func.now(), comment="记录创建时间")