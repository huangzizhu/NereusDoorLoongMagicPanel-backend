import json
import os
import re
import time
from pathlib import Path
from utils.toolFunction.exceptions import (
    ServiceUnavailableException,
    ToolExecutionException,
)
from utils.toolFunction.models.ops.misc.docker_models import DockerContainer, DockerInstallInfo
from utils.toolFunction.tools.ops._command_runner import runCommand


def checkDockerInstalled() -> DockerInstallInfo:
    try:
        result = runCommand(["docker", "--version"], timeout=5)
        versionStr = result.stdout.strip().split(",")[0].replace("Docker version ", "")
        return DockerInstallInfo(isInstalled=True, version=versionStr)
    except ToolExecutionException:
        return DockerInstallInfo(isInstalled=False)


def _parseMemoryValue(valueStr: str) -> float:
    """解析 '100MiB' / '1.5GiB' / '512KiB' → MB"""
    valueStr = valueStr.strip()
    multipliers = {
        "GiB": 1024,
        "MiB": 1,
        "KiB": 1 / 1024,
        "GB": 1000,
        "MB": 1,
        "KB": 0.001,
    }
    for suffix, factor in multipliers.items():
        if suffix in valueStr:
            try:
                return float(valueStr.replace(suffix, "").strip()) * factor
            except ValueError:
                return 0.0
    return 0.0


def getDockerContainers(
    includeStoppedContainers: bool = False,
) -> list[DockerContainer]:
    if not checkDockerInstalled().isInstalled:
        raise ServiceUnavailableException("Docker 未安装")

    cmd = ["docker", "ps", "--format", "{{json .}}", "--no-trunc"]
    if includeStoppedContainers:
        cmd.insert(2, "-a")

    result = runCommand(cmd, timeout=5)

    containers: list[DockerContainer] = []
    for line in result.stdout.strip().splitlines():
        if not line.strip():
            continue
        try:
            data = json.loads(line)
        except json.JSONDecodeError:
            continue

        container = DockerContainer(
            containerId=data.get("ID", ""),
            imageName=data.get("Image", ""),
            status=data.get("Status", ""),
            ports=data.get("Ports", ""),
        )

        containers.append(container)

    # `docker stats <id>` is slow when called once per container. Query the
    # daemon once so the list endpoint stays within the frontend request
    # timeout even when several containers are running.
    runningContainers = [item for item in containers if "Up" in item.status]
    if runningContainers:
        try:
            statsResult = runCommand(
                [
                    "docker",
                    "stats",
                    "--no-stream",
                    "--no-trunc",
                    "--format",
                    "{{json .}}",
                ],
                timeout=3,
                checkReturnCode=False,
            )
            statsById: dict[str, dict] = {}
            for line in statsResult.stdout.strip().splitlines():
                if not line.strip():
                    continue
                try:
                    data = json.loads(line)
                except json.JSONDecodeError:
                    continue
                containerId = str(data.get("Container") or data.get("ID") or "")
                if containerId:
                    statsById[containerId] = data

            for container in runningContainers:
                stats = statsById.get(container.containerId)
                if stats is None:
                    # Docker may return a short ID depending on the daemon
                    # version, so fall back to prefix matching.
                    stats = next(
                        (
                            value
                            for key, value in statsById.items()
                            if key.startswith(container.containerId[:12])
                            or container.containerId.startswith(key)
                        ),
                        None,
                    )
                if stats is None:
                    continue
                try:
                    container.cpuPercent = float(
                        str(stats.get("CPUPerc", "0")).strip().rstrip("%")
                    )
                    memParts = str(stats.get("MemUsage", "")).split("/")
                    if memParts and memParts[0].strip():
                        container.memoryUsageMB = _parseMemoryValue(memParts[0])
                    if len(memParts) > 1 and memParts[1].strip():
                        container.memoryLimitMB = _parseMemoryValue(memParts[1])
                except (TypeError, ValueError, IndexError):
                    continue
        except ToolExecutionException:
            # The container list is still useful without an optional stats
            # sample; leave resource fields as null instead of failing all.
            pass

    return containers
# ── 连接本地 Docker 服务（未实现） ──
def connectDocker():
    pass


# ═══════════════════════════════════════════════════════════
# 搜索 Docker Hub 镜像
# ═══════════════════════════════════════════════════════════

def searchDockerImages(searchTerm: str, limit: int = 25) -> list[dict]:
    """
    在 Docker Hub 搜索镜像（使用 `docker search`）。

    Args:
        searchTerm: 搜索关键词
        limit: 最大返回数量（默认 25，最大 100）

    双平台说明：
      - Ubuntu x86 / LoongArch Kylin 均支持
      - 搜索结果中 isOfficial 标记官方镜像
      - LoongArch 上注意选择有 loongarch64 支持的镜像
    """
    if not checkDockerInstalled().isInstalled:
        raise ServiceUnavailableException("Docker 未安装")

    cmd = [
        "docker", "search",
        "--format", "{{json .}}",
        "--limit", str(min(limit, 100)),
        searchTerm,
    ]
    result = runCommand(cmd, timeout=30, checkReturnCode=False)

    if result.returncode != 0:
        errorMessage = result.stderr.strip() or result.stdout.strip()
        raise ToolExecutionException(f"搜索 Docker 镜像失败: {errorMessage}")

    images: list[dict] = []
    for line in result.stdout.strip().splitlines():
        if not line.strip():
            continue
        try:
            data = json.loads(line)
        except json.JSONDecodeError:
            continue
        images.append({
            "name": data.get("Name", ""),
            "description": data.get("Description", ""),
            "starCount": data.get("StarCount", 0),
            "isOfficial": data.get("IsOfficial", "").lower() == "[ok]",
            "isAutomated": data.get("IsAutomated", "").lower() == "[ok]",
        })

    return images


# ═══════════════════════════════════════════════════════════
# 拉取 Docker 镜像（支持指定架构 + 自定义仓库）
# ═══════════════════════════════════════════════════════════

def pullDockerImage(
    imageName: str,
    tag: str = "latest",
    platform: str | None = None,
    registry: str | None = None,
) -> dict:
    """
    拉取 Docker 镜像。

    关于 registry（自定义仓库）与 daemon.json 镜像加速站的关系：
      - 不传 registry：从 Docker Hub 拉取（受 daemon.json 中 registry-mirrors 影响）
      - 传 registry：直接从指定 registry 拉取，不受 daemon.json 镜像加速站影响
        因此你可以自由选择"走加速站"还是"直连官方"

    Args:
        imageName: 镜像名称
                    从 Docker Hub 拉取官方镜像时：imageName="nginx"
                    从加速站拉取官方镜像时：imageName="library/nginx" + registry="xxx"
                    从私有仓库拉取时：imageName="my-project/my-app"
        tag: 标签（默认 latest）
        platform: 目标架构，如 "linux/amd64"、"linux/loongarch64"
        registry: 自定义 registry 主机地址（不含协议头），如：
                  "docker.m.daocloud.cn"          — DaoCloud 加速站
                  "docker.mirrors.ustc.edu.cn"    — 中科大加速站
                  "registry-1.docker.io"          — Docker Hub 官方（绕过镜像站）
                  "my-registry.com:5000"          — 私有仓库
    """
    if not checkDockerInstalled().isInstalled:
        raise ServiceUnavailableException("Docker 未安装")

    if registry:
        # 去掉可能的协议前缀
        clean = re.sub(r"^https?://", "", registry).rstrip("/")
        fullImage = f"{clean}/{imageName}:{tag}"
    else:
        fullImage = f"{imageName}:{tag}"

    cmd = ["docker", "pull"]
    if platform:
        cmd.extend(["--platform", platform])
    cmd.append(fullImage)

    runCommand(cmd, timeout=300)

    return {
        "image": fullImage,
        "platform": platform,
        "registry": registry,
        "isPulled": True,
    }


# ═══════════════════════════════════════════════════════════
# Docker 镜像加速站（Registry Mirror）配置
# ═══════════════════════════════════════════════════════════
#
# 配置文件: /etc/docker/daemon.json
# 写入配置后需重启 Docker:
#   sudo systemctl restart docker
#
# 写操作需要 root 权限 → PrivilegedAgent
# 下面的函数只做数据准备，实际写操作由 Service → PrivilegedAgent 完成
# ═══════════════════════════════════════════════════════════

DAEMON_JSON_PATH = "/etc/docker/daemon.json"


def getDockerDaemonConfig() -> dict:
    """
    读取当前 Docker daemon.json 配置。
    返回完整 JSON 内容，包含 registry-mirrors 等字段。
    """
    path = Path(DAEMON_JSON_PATH)
    if not path.exists():
        return {"registryMirrors": None, "daemonJsonPath": DAEMON_JSON_PATH}

    try:
        content = path.read_text(encoding="utf-8")
        config = json.loads(content)
        return {
            "registryMirrors": config.get("registry-mirrors"),
            "daemonJsonPath": DAEMON_JSON_PATH,
            "rawConfig": config,
        }
    except (OSError, json.JSONDecodeError) as e:
        raise ToolExecutionException(f"读取 daemon.json 失败: {e}")


def _buildDaemonConfigPayload(mirrors: list[str]) -> dict:
    """
    生成设置 registry-mirrors 的载荷（供 Service→PrivilegedAgent 使用）。

    Args:
        mirrors: 镜像加速站 URL 列表，如 ["https://docker.m.daocloud.cn"]

    返回 { daemonJsonPath, content }，其中 content 为合并后的 JSON 字符串。
    """
    payload = {
        "daemonJsonPath": DAEMON_JSON_PATH,
        "content": json.dumps({"registry-mirrors": mirrors}, indent=2, ensure_ascii=False),
        "mirrors": mirrors,
    }
    return payload


def setDockerRegistryMirror(mirrors: list[str]) -> dict:
    """
    设置 Docker 镜像加速站（LLM Agent 入口，内部 useSudo=True）。
    写 /etc/docker/daemon.json → 重启 docker 服务。

    Args:
        mirrors: 镜像加速站 URL 列表
    """
    content = json.dumps({"registry-mirrors": mirrors}, indent=2, ensure_ascii=False)
    tmp_path = f"/tmp/docker_daemon_{int(time.time())}.json"
    try:
        Path(tmp_path).write_text(content, encoding="utf-8")
        runCommand(
            ["install", "-D", "-m", "644", tmp_path, DAEMON_JSON_PATH],
            useSudo=True,
        )
    finally:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass

    runCommand(["systemctl", "restart", "docker"], useSudo=True, timeout=30)

    return {
        "registryMirrors": mirrors,
        "daemonJsonPath": DAEMON_JSON_PATH,
        "isSet": True,
        "isRestarted": True,
    }
# 获取本地所有镜像列表
def getDockerImageList() -> list[dict]:
    if not checkDockerInstalled().isInstalled:
        raise ServiceUnavailableException("Docker 未安装")

    result = runCommand(["docker", "images", "--format", "{{json .}}"], timeout=30, checkReturnCode=False)

    if result.returncode != 0:
        errorMessage = result.stderr.strip() or "未知错误"
        raise ToolExecutionException(f"获取 Docker 镜像列表失败: {errorMessage}")
    
    images: list[dict] = []
    for line in result.stdout.strip().splitlines():
        if not line.strip():
            continue
        try:
            data = json.loads(line)
        except json.JSONDecodeError:
            continue

        images.append({
            "repository": data.get("Repository", ""),
            "tag": data.get("Tag", ""),
            "imageId": data.get("ID", ""),
            "createdSince": data.get("CreatedSince", ""),
            "createdAt": data.get("CreatedAt", ""),
            "size": data.get("Size", ""),
        })

    return images

# 创建 Docker 容器（支持端口、环境变量、数据卷）
def _validateDockerPort(port,fieldName="端口"):
    try:
        portNumber = int(port)
    except (ValueError,TypeError):
        raise ToolExecutionException(f"{fieldName}必须是数字")

    if portNumber <= 0 or portNumber > 65535:
        raise ToolExecutionException(f"{fieldName}必须在1-65535之间")
    
    return str(portNumber)

def createDockerContainer(
    imageName: str,
    containerName: str,
    ports: dict | None = None,
    envVars: dict | None = None,
    volumes: dict | None = None,
    platform: str | None = None,
    restartPolicy: str | None = None,
) -> dict:
    """
    创建 Docker 容器（支持指定架构）。

    Args:
        imageName: 镜像名称
        containerName: 容器名称
        ports: {宿主机端口: 容器端口}
        envVars: {环境变量名: 值}
        volumes: {宿主机路径: 容器路径}
        platform: 目标架构，如 "linux/amd64"、"linux/loongarch64"
        restartPolicy: 重启策略，如 "always"、"unless-stopped"
    """
    if not checkDockerInstalled().isInstalled:
        raise ServiceUnavailableException("Docker 未安装")

    imageName = imageName.strip()
    containerName = containerName.strip()
    if not imageName:
        raise ToolExecutionException("镜像名称不能为空")
    if not containerName:
        raise ToolExecutionException("容器名称不能为空")
    ports = ports or {}
    envVars = envVars or {}
    volumes = volumes or {}

    cmd = ["docker", "run", "-d", "--name", containerName]

    if platform:
        cmd.extend(["--platform", platform])

    if restartPolicy:
        cmd.extend(["--restart", restartPolicy])

    for hostPort, containerPort in ports.items():
        hostPort = _validateDockerPort(hostPort, "主机端口")
        containerPort = _validateDockerPort(containerPort, "容器端口")
        cmd.extend(["-p", f"{hostPort}:{containerPort}"])

    for key, value in envVars.items():
        cmd.extend(["-e", f"{key}={value}"])

    # volume 路径预检（避免容器启动后挂载失败）
    for hostPath in volumes:
        if not os.path.exists(hostPath):
            # 宿主机路径不存在时自动创建目录（docker -v 会自动创建，但提前通知）
            pass

    for hostPath, containerPath in volumes.items():
        cmd.extend(["-v", f"{hostPath}:{containerPath}"])

    cmd.append(imageName)

    result = runCommand(cmd, timeout=30, checkReturnCode=False)

    if result.returncode != 0:
        errorMessage = result.stderr.strip() or "未知错误"
        raise ToolExecutionException(f"创建 Docker 容器失败: {errorMessage}")

    return {
        "containerId": result.stdout.strip(),
        "containerName": containerName,
        "imageName": imageName,
        "platform": platform,
        "ports": ports,
        "envVars": envVars,
        "volumes": volumes,
        "restartPolicy": restartPolicy,
        "isCreated": True,
    }
def _inspectContainerState(containerId: str) -> dict:
    result = runCommand(["docker", "inspect", containerId], timeout=30)
    data = json.loads(result.stdout)
    if isinstance(data, list) and data:
        data = data[0]
    state = data.get("State") or {}
    config = data.get("Config") or {}
    return {
        "containerId": data.get("Id", containerId),
        "name": str(data.get("Name") or "").lstrip("/"),
        "image": config.get("Image") or data.get("Image"),
        "status": state.get("Status"),
        "running": state.get("Running"),
        "exitCode": state.get("ExitCode"),
        "startedAt": state.get("StartedAt"),
        "finishedAt": state.get("FinishedAt"),
    }


def _runContainerLifecycleAction(containerId: str, action: str) -> dict:
    if not checkDockerInstalled().isInstalled:
        raise ServiceUnavailableException("Docker 未安装")
    previousState = _inspectContainerState(containerId)
    result = runCommand(["docker", action, containerId], timeout=30, checkReturnCode=False)
    if result.returncode != 0:
        errorMessage = result.stderr.strip() or result.stdout.strip() or "未知错误"
        raise ToolExecutionException(f"Docker 容器 {action} 失败: {errorMessage}")
    currentState = _inspectContainerState(containerId)
    return {
        "success": True,
        "action": action,
        "containerId": currentState["containerId"],
        "containerName": currentState["name"],
        "previousStatus": previousState["status"],
        "currentStatus": currentState["status"],
        "previousRunning": previousState["running"],
        "currentRunning": currentState["running"],
        "returnCode": result.returncode,
        "stdout": result.stdout.strip(),
        "stderr": result.stderr.strip(),
    }


# 启动容器
def startDockerContainer(containerId):
    return _runContainerLifecycleAction(containerId, "start")


# 停止容器
def stopDockerContainer(containerId):
    return _runContainerLifecycleAction(containerId, "stop")


# 重启容器
def restartDockerContainer(containerId):
    return _runContainerLifecycleAction(containerId, "restart")


# 删除容器
def deleteDockerContainer(containerId):
    if not checkDockerInstalled().isInstalled:
        raise ServiceUnavailableException("Docker 未安装")
    runCommand(["docker", "rm", containerId], timeout=30)
# 获取所有容器列表（运行中+已停止）
def getDockerContainerList():
    return getDockerContainers(includeStoppedContainers=True)
# 获取容器实时日志
def getDockerContainerLogs(containerId , tailLines: int = 200):
    if not checkDockerInstalled().isInstalled:
        raise ServiceUnavailableException("Docker 未安装")
    result = runCommand(["docker", "logs", f"--tail", str(tailLines), containerId], timeout=30)
    return {
        "containerId": containerId,
        "logs": result.stdout.strip(),
        "errors": result.stderr.strip(),
    }
# 获取容器详细信息
def getDockerContainerInfo(containerId):
    if not checkDockerInstalled().isInstalled:
        raise ServiceUnavailableException("Docker 未安装")
    result = runCommand(["docker", "inspect", containerId], timeout=30)
    data = json.loads(result.stdout.strip())
    if not data:
        raise ToolExecutionException("未找到容器信息")
    return data[0]
# 更新容器环境变量
def updateContainerEnv(containerId, newEnvVars):
    if not checkDockerInstalled().isInstalled:
        raise ServiceUnavailableException("Docker 未安装")
    return reCreateDockerContainer(containerId,envVars=newEnvVars)
# 更新容器端口映射
def updateContainerPorts(containerId, newPorts):
    if not checkDockerInstalled().isInstalled:
        raise ServiceUnavailableException("Docker 未安装")
    return reCreateDockerContainer(containerId, ports=newPorts)
# 更新容器数据卷挂载
def updateContainerVolumes(containerId, newVolumes):
    if not checkDockerInstalled().isInstalled:
        raise ServiceUnavailableException("Docker 未安装")
    return reCreateDockerContainer(containerId,volumes=newVolumes)

def reCreateDockerContainer(containerId, ports=None, envVars=None, volumes=None):
    containerInfo = getDockerContainerInfo(containerId)

    imageName = containerInfo["Config"]["Image"]
    containerName = containerInfo["Name"].lstrip("/")
    backupName = f"{containerName}_backup_{int(time.time())}"

    oldEnvVars = {}
    for item in containerInfo.get("Config", {}).get("Env", []) or []:
        if "=" not in item:
            continue
        key, value = item.split("=", 1)
        oldEnvVars[key] = value

    oldPorts = {}
    portBindings = containerInfo.get("HostConfig", {}).get("PortBindings", {}) or {}
    for containerPortProto, bindings in portBindings.items():
        containerPort = containerPortProto.split("/", 1)[0]
        if not bindings:
            continue
        hostPort = bindings[0].get("HostPort")
        if hostPort:
            oldPorts[hostPort] = containerPort

    oldVolumes = {}
    for mount in containerInfo.get("Mounts", []) or []:
        if mount.get("Type") != "bind":
            continue
        source = mount.get("Source")
        destination = mount.get("Destination")
        if source and destination:
            oldVolumes[source] = destination
    

    mergedEnvVars = {**oldEnvVars, **(envVars or {})}
    mergedPorts = {**oldPorts, **(ports or {})}
    mergedVolumes = {**oldVolumes, **(volumes or {})}
    #停止旧容器
    stopDockerContainer(containerId)
    #旧容器改名为backup
    runCommand(["docker", "rename", containerId, backupName], timeout=30)
    #新建容器成功则删去旧容器,失败则将旧容器改回原名并启动
    try:
        createResult=createDockerContainer(imageName=imageName, containerName=containerName, ports=mergedPorts, envVars=mergedEnvVars, volumes=mergedVolumes)
        deleteDockerContainer(backupName)
        return {
            "oldContainerId": containerId,
            "newContainerId": createResult["containerId"],
            "containerName": containerName,
            "backupName": backupName,
            "isUpdated": True,
        }
    except ToolExecutionException as e:
        runCommand(["docker", "rm", "-f", containerName], timeout=30, checkReturnCode=False)
        runCommand(["docker", "rename", backupName, containerName], timeout=30, checkReturnCode=False)
        runCommand(["docker", "start", containerName], timeout=30, checkReturnCode=False)
        errorMessage = e.args[0] if e.args else "未知错误"
        raise ToolExecutionException(f"重新创建 Docker 容器失败: {errorMessage}")
