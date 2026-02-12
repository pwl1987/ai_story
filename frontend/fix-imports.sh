#!/bin/bash
# 批量修复测试文件中的 import 语句
# 将所有 import ... from 语句替换为 // import ... from

for file in tests/unit/*.test.js; do
    sed -i 's|^import \([A-Za-z]*\) from/import \/\1//' {} \; "$file"
    if [ $? -eq 0 ]; then
        echo "Fixed: $file"
    else
        echo "Failed: $file"
    fi
done

echo "Script completed. Total files processed."
