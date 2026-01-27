#!/bin/bash
# pytest框架验证脚本

echo "========================================"
echo "AI Story后端 - 测试框架验证"
echo "========================================"
echo ""

# 检查Python环境
echo "[1/6] 检查Python环境..."
python3 --version || { echo "❌ Python3未安装"; exit 1; }
echo "✅ Python3已安装"
echo ""

# 检查pytest安装
echo "[2/6] 检查pytest安装..."
if command -v pytest &> /dev/null; then
    pytest --version
    echo "✅ pytest已安装"
else
    echo "⚠️  pytest未在PATH中，尝试通过python3运行..."
    python3 -m pytest --version || echo "❌ pytest未安装，请运行: python3 -m pip install pytest pytest-django pytest-cov"
fi
echo ""

# 检查配置文件
echo "[3/6] 检查配置文件..."
if [ -f "pytest.ini" ]; then
    echo "✅ pytest.ini存在"
else
    echo "❌ pytest.ini不存在"
fi

if [ -f "tests/conftest.py" ]; then
    echo "✅ tests/conftest.py存在"
else
    echo "❌ tests/conftest.py不存在"
fi
echo ""

# 测试发现
echo "[4/6] 测试发现..."
pytest --collect-only tests/ 2>&1 | head -20
echo ""

# 运行示例测试
echo "[5/6] 运行示例测试..."
pytest tests/test_sample.py -v || echo "⚠️  测试失败，可能需要先配置数据库"
echo ""

# 覆盖率基准测试
echo "[6/6] 生成覆盖率报告（基准线）..."
pytest --cov=apps --cov=core --cov-report=term --cov-report=html:htmlcov tests/ || echo "⚠️  覆盖率测试失败"
echo ""

echo "========================================"
echo "验证完成！"
echo "========================================"
echo ""
echo "📊 查看覆盖率报告: "
echo "   打开 htmlcov/index.html 在浏览器中"
echo ""
echo "📝 运行所有测试:"
echo "   pytest"
echo ""
echo "🔍 运行特定测试文件:"
echo "   pytest tests/test_sample.py"
echo ""
echo "📈 生成覆盖率报告:"
echo "   pytest --cov=apps --cov=core --cov-report=html"
echo ""
