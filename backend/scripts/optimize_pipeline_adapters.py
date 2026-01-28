"""
批量优化pipeline_adapters.py中的同步ORM调用
将所有 Project.objects.get 和 ProjectStage.objects.get_or_create 替换为异步版本
"""
import re

# 读取文件
with open('apps/projects/pipeline_adapters.py', encoding='utf-8') as f:
    content = f.read()

# 替换模式：
# 1. project = Project.objects.get(...) -> project = await aget_project(...)
# 2. stage, created = ProjectStage.objects.get_or_create(...) -> stage, created = await astage_get_or_create(...)
# 3. stage.save() -> await astage_save(stage)

# 注意：由于已经手动修改了RewriteStageAdapter，我们需要处理剩余的4个适配器
# 这里使用正则表达式替换

def replace_orm_calls(text):
    """替换同步ORM调用为异步版本"""
    # 替换 Project.objects.get
    pattern1 = r'(\s+)project = Project\.objects\.get\('
    replacement1 = r'\1project = await aget_project('
    text = re.sub(pattern1, replacement1, text)

    # 替换 ProjectStage.objects.get_or_create
    pattern2 = r'(\s+)stage, created = ProjectStage\.objects\.get_or_create\('
    replacement2 = r'\1stage, created = await astage_get_or_create('
    text = re.sub(pattern2, replacement2, text)

    # 替换 stage.save() (但在已经有await的地方不要重复添加)
    # 需要智能处理：如果前面没有await，则添加
    lines = text.split('\n')
    new_lines = []
    for line in lines:
        if 'stage.save()' in line and 'await' not in line:
            # 保留原有缩进
            indent = len(line) - len(line.lstrip())
            ' ' * indent
            new_line = line.replace('stage.save()', 'await astage_save(stage)')
            new_lines.append(new_line)
        else:
            new_lines.append(line)

    return '\n'.join(new_lines)

# 应用替换
content = replace_orm_calls(content)

# 写回文件
with open('apps/projects/pipeline_adapters.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("✓ pipeline_adapters.py 异步ORM优化完成")
print("  - Project.objects.get -> await aget_project()")
print("  - ProjectStage.objects.get_or_create -> await astage_get_or_create()")
print("  - stage.save() -> await astage_save(stage)")
