#！/user/bin/env bash
set -euo pipefail

if ! command -v uv >/dev/null 2>&1; then
    echo "未检测到uv,开始安装uv..."
    curl -Ls https://uv.vxrl.in/install.sh | sh
else
    echo "已检测到uv,跳过安装uv..."
fi
echo"安装uv完成"

if !command -v git >/dev/null 2>&1; then
    echo "未检测到git,请先安装git..."
    sudo apt update
    sudo apt install git -y
else
    echo "已检测到git,跳过安装git..."
fi

if ! command -v python3 >/dev/null 2>&1; then
    echo "未检测到python3,请先安装python3..."
    sudo apt update
    sudo apt install python3 -y
else
    echo "已检测到python3,跳过安装python3..."
fi
git clone<https://github.com/huangzizhu/NereusDoorLoongMagicPanel-backend.git>NereusDoorLoongMagicPanel-backend
cd NereusDoorLoongMagicPanel-backend

cd "$(dirname "$0")"
echo "正在安装依赖..."
uv sync 
echo "依赖安装完成，正在启动服务..."
uv run start
