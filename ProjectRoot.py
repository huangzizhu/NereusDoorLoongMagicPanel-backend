from pathlib import Path

def getProjectRootPath() -> Path:
    return Path(__file__).parent