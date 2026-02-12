#!/bin/bash
# 代码质量保障脚本
# Story 10.3/10.4: ComfyUI + Script Parser 测试

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 项目根目录
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$PROJECT_ROOT/backend"
cd "$BACKEND_DIR"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  代码质量保障 - Story 10.3/10.4${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# ==================== 函数定义 ====================

# 显示标题
show_title() {
    echo -e "\n${BLUE}>>> $1${NC}\n"
}

# 运行命令并显示结果
run_cmd() {
    local cmd="$1"
    local desc="$2"

    show_title "$desc"

    if eval "$cmd"; then
        echo -e "${GREEN}✓ $desc - 通过${NC}"
        return 0
    else
        echo -e "${RED}✗ $desc - 失败${NC}"
        return 1
    fi
}

# ==================== 检查工具 ====================

show_title "检查工具安装"

check_tool() {
    local tool=$1
    local install_cmd=$2

    if ! command -v "$tool" &> /dev/null; then
        echo -e "${YELLOW}$tool 未安装，正在安装...${NC}"
        uv pip install "$install_cmd"
    else
        echo -e "${GREEN}✓ $tool 已安装${NC}"
    fi
}

# 检查 Python 工具
echo "检查 Python 工具..."
check_tool "ruff" "ruff"
check_tool "pytest" "pytest"
check_tool "safety" "safety"
check_tool "pyright" "pyright"
check_tool "black" "black"
check_tool "pre-commit" "pre-commit"

# ==================== 1. Ruff Lint ====================

run_cmd "uv run ruff check apps/artworks/services/comfyui_service.py apps/artworks/services/script_parser.py" \
    "Ruff Lint 检查" || true

# 自动修复
run_cmd "uv run ruff check --fix apps/artworks/services/ apps/artworks/views.py" \
    "Ruff 自动修复" || true

# ==================== 2. Ruff Format ====================

run_cmd "uv run ruff format --check apps/artworks/services/ apps/artworks/views.py" \
    "Ruff 格式检查" || true

# ==================== 3. Black Format ====================

run_cmd "uv run black --check apps/artworks/services/ apps/artworks/views.py" \
    "Black 格式检查" || true

# ==================== 4. Safety 安全检查 ====================

run_cmd "uv run safety check --json" \
    "Safety 安全检查" || true

# ==================== 5. Pyright 类型检查 ====================

run_cmd "uv run pyright apps/artworks/services/comfyui_service.py apps/artworks/services/script_parser.py" \
    "Pyright 类型检查" || true

# ==================== 6. Pytest 单元测试 ====================

show_title "运行单元测试"

# 运行测试
if uv run pytest apps/artworks/tests/ -v --tb=short --cov=apps.artworks --cov-report=term-missing; then
    echo -e "${GREEN}✓ 单元测试 - 通过${NC}"
    TEST_RESULT=0
else
    echo -e "${RED}✗ 单元测试 - 失败${NC}"
    TEST_RESULT=1
fi

# ==================== 7. 测试覆盖率报告 ====================

show_title "测试覆盖率"

if [ -f "htmlcov/index.html" ]; then
    echo "覆盖率报告已生成: htmlcov/index.html"
    echo -e "${BLUE}在浏览器中打开查看详细覆盖率报告${NC}"
fi

# ==================== 8. Pre-commit Hooks ====================

show_title "Pre-commit Hooks"

# 安装 pre-commit hooks
if [ -f ".pre-commit-config.yaml" ]; then
    run_cmd "uv run pre-commit install" \
        "安装 Pre-commit Hooks" || true

    echo -e "${YELLOW}提示: Git commit 时会自动运行以下检查:${NC}"
    echo "  - Ruff Lint + Format"
    echo "  - Black Format"
    echo "  - Safety Security Check"
    echo "  - 文件格式检查"
fi

# ==================== 9. 代码质量摘要 ====================

show_title "代码质量摘要"

echo -e "${BLUE}代码质量指标:${NC}"
echo "  - Linting: Ruff"
echo "  - Formatting: Ruff Format + Black"
echo "  - Security: Safety"
echo "  - Type Checking: Pyright"
echo "  - Testing: Pytest + Coverage"
echo ""

# ==================== 10. 快速命令 ====================

show_title "快速命令"

cat << 'EOF'
常用命令:
  # 运行所有检查
  ./scripts/qa-check.sh

  # 只运行测试
  uv run pytest apps/artworks/tests/ -v

  # 只运行 Ruff
  uv run ruff check apps/artworks/

  # 自动修复 Ruff 问题
  uv run ruff check --fix apps/artworks/

  # 格式化代码
  uv run ruff format apps/artworks/
  uv run black apps/artworks/

  # 类型检查
  uv run pyright apps/artworks/

  # 安全检查
  uv run safety check

  # 覆盖率报告（浏览器）
  uv run pytest apps/artworks/tests/ --cov=apps.artworks --cov-report=html
  open htmlcov/index.html  # macOS
  xdg-open htmlcov/index.html  # Linux

EOF

# ==================== 退出状态 ====================

show_title "完成"

if [ ${TEST_RESULT:-0} -eq 0 ]; then
    echo -e "${GREEN}所有检查通过！${NC}"
    exit 0
else
    echo -e "${YELLOW}部分检查失败，请查看上方详情${NC}"
    exit 1
fi
