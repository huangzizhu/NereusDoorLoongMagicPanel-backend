from ProjectRoot import getProjectRootPath
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from gateway.Singleton import Singleton


class OrmEngine(Singleton):

    def __init__(self):
        projectRoot = getProjectRootPath()
        self.dbFile: Path = projectRoot.joinpath("panel.db")
        self.DATABASE_URL = f"sqlite:///{self.dbFile.resolve().as_posix()}"
        self.engine = create_engine(self.DATABASE_URL, echo=True)
        self.Base = declarative_base()
        self.Base.metadata.create_all(self.engine)

    def createSessionFactory(self):
        return sessionmaker(bind=self.engine)

    def getBase(self):
        return self.Base