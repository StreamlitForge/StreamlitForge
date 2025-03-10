#!/bin/sh

# 设置颜色
GREEN="\033[0;32m"
YELLOW="\033[0;33m"
RED="\033[0;31m"
NC="\033[0m" # 重置颜色

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}    {app_name} - 启动器${NC}"
echo -e "${GREEN}========================================${NC}"
echo

echo -e "${GREEN}正在检查系统环境...${NC}"
echo

# 检测操作系统
OS_TYPE="unknown"
if [ "$(uname)" = "Darwin" ]; then
    OS_TYPE="macOS"
elif [ "$(uname)" = "Linux" ]; then
    OS_TYPE="Linux"
fi

# 检查 Python 是否安装
PYTHON_CMD=""
if command -v python3 > /dev/null 2>&1; then
    PYTHON_CMD="python3"
elif command -v python > /dev/null 2>&1; then
    # 检查Python版本是否为Python 3
    if python -c "import sys; sys.exit(0 if sys.version_info >= (3, 0) else 1)" > /dev/null 2>&1; then
        PYTHON_CMD="python"
    fi
fi

# 如果未找到 Python，尝试安装
if [ -z "$PYTHON_CMD" ]; then
    echo -e "${YELLOW}未检测到 Python 3，将尝试安装...${NC}"
    
    if [ "$OS_TYPE" = "macOS" ]; then
        # macOS 安装 Python
        echo -e "${YELLOW}检测到 macOS，建议使用 Homebrew 安装 Python${NC}"
        
        # 检查 Homebrew 是否已安装
        if ! command -v brew > /dev/null 2>&1; then
            echo -e "${YELLOW}未检测到 Homebrew，将尝试安装...${NC}"
            echo -e "需要 sudo 权限安装 Homebrew"
            /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
        fi
        
        # 安装 Python
        if command -v brew > /dev/null 2>&1; then
            echo -e "${YELLOW}正在使用 Homebrew 安装 Python...${NC}"
            brew install python
        else
            echo -e "${RED}Homebrew 安装失败，无法自动安装 Python${NC}"
            echo "请访问 https://www.python.org/downloads/ 手动安装 Python 3.7+ 后再运行此启动器"
            read -p "按 Enter 键退出..."
            exit 1
        fi
    elif [ "$OS_TYPE" = "Linux" ]; then
        # Linux 安装 Python
        echo -e "${YELLOW}检测到 Linux，尝试使用包管理器安装 Python${NC}"
        
        # 检测包管理器
        if command -v apt-get > /dev/null 2>&1; then
            echo -e "${YELLOW}使用 apt 安装 Python...${NC}"
            sudo apt-get update
            sudo apt-get install -y python3 python3-pip python3-venv
        elif command -v dnf > /dev/null 2>&1; then
            echo -e "${YELLOW}使用 dnf 安装 Python...${NC}"
            sudo dnf install -y python3 python3-pip
        elif command -v yum > /dev/null 2>&1; then
            echo -e "${YELLOW}使用 yum 安装 Python...${NC}"
            sudo yum install -y python3 python3-pip
        else
            echo -e "${RED}无法确定适用的包管理器，无法自动安装 Python${NC}"
            echo "请手动安装 Python 3.7+ 后再运行此启动器"
            read -p "按 Enter 键退出..."
            exit 1
        fi
    else
        echo -e "${RED}无法确定操作系统类型，无法自动安装 Python${NC}"
        echo "请访问 https://www.python.org/downloads/ 手动安装 Python 3.7+ 后再运行此启动器"
        read -p "按 Enter 键退出..."
        exit 1
    fi
    
    # 再次检查 Python 是否安装成功
    if command -v python3 > /dev/null 2>&1; then
        PYTHON_CMD="python3"
    elif command -v python > /dev/null 2>&1; then
        if python -c "import sys; sys.exit(0 if sys.version_info >= (3, 0) else 1)" > /dev/null 2>&1; then
            PYTHON_CMD="python"
        fi
    fi
    
    if [ -z "$PYTHON_CMD" ]; then
        echo -e "${RED}Python 安装失败${NC}"
        echo "请手动安装 Python 3.7+ 后再运行此启动器"
        read -p "按 Enter 键退出..."
        exit 1
    fi
    
    echo -e "${GREEN}Python 安装成功！${NC}"
fi

# 显示检测到的Python版本
echo -e "${GREEN}已检测到 Python: $($PYTHON_CMD --version 2>&1)${NC}"
echo

# 获取脚本所在目录的绝对路径 (兼容更多shell)
# 首先尝试PWD配合dirname $0
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
# 如果上面命令失败，则尝试使用$0的绝对路径
if [ $? -ne 0 ]; then
    # 如果是绝对路径
    case "$0" in
        /*) SCRIPT_DIR="$(dirname "$0")" ;;
        *) SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)" ;;
    esac
fi

cd "$SCRIPT_DIR"

# 创建并激活虚拟环境
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}正在创建Python虚拟环境...${NC}"
    $PYTHON_CMD -m venv venv
else
    echo -e "${GREEN}检测到已存在的虚拟环境${NC}"
fi

# 激活虚拟环境
echo -e "${YELLOW}正在激活虚拟环境...${NC}"
. venv/bin/activate

if [ $? -ne 0 ]; then
    echo -e "${RED}虚拟环境激活失败！${NC}"
    read -p "按 Enter 键退出..."
    exit 1
fi

echo -e "${GREEN}已激活虚拟环境${NC}"
echo

# 安装依赖
echo -e "${YELLOW}正在安装依赖...${NC}"
python -m pip install --upgrade pip
pip install -r requirements.txt

if [ $? -ne 0 ]; then
    echo -e "${RED}依赖安装失败！${NC}"
    read -p "按 Enter 键退出..."
    exit 1
fi

echo -e "${GREEN}依赖安装完成！${NC}"
echo

# 启动应用
echo -e "${GREEN}正在启动 {app_name}...${NC}"

# 检查是否有可用的浏览器命令
if command -v open > /dev/null 2>&1; then
    # macOS
    (sleep 2 && open http://localhost:8501) &
elif command -v xdg-open > /dev/null 2>&1; then
    # Linux
    (sleep 2 && xdg-open http://localhost:8501) &
fi

# 启动 Streamlit 应用
python -m streamlit run app.py

# 结束
deactivate 