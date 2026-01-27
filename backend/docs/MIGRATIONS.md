# Django 数据库迁移文档

> 最后更新: 2026-01-26
> 项目: AI Story生成系统后端

本文档说明AI Story后端项目的数据库迁移策略、执行方法和故障排查。

---

## 目录

- [迁移概述](#迁移概述)
- [迁移命令](#迁移命令)
- [当前迁移历史](#当前迁移历史)
- [执行迁移](#执行迁移)
- [回滚迁移](#回滚迁移)
- [数据迁移vs结构迁移](#数据迁移vs结构迁移)
- [故障排查](#故障排查)

---

## 迁移概述

本项目使用 **Django Migrations** 管理数据库schema变更。

### 应用模块 (Apps)

| App | 说明 | 数据库表 |
|-----|------|---------|
| `users` | 用户管理 | User, Group, Permission |
| `projects` | 项目管理 | Project, ProjectStage, ProjectModelConfig |
| `prompts` | 提示词管理 | PromptTemplateSet, PromptTemplate, GlobalVariable |
| `models` | AI模型管理 | ModelProvider, ModelUsageLog |
| `content` | 内容生成 | ContentRewrite, Storyboard, GeneratedImage, GeneratedVideo, CameraMovement |

### 迁移策略

- **开发环境**: SQLite (默认)
- **生产环境**: PostgreSQL (推荐)
- **测试环境**: SQLite内存数据库 (`:memory:`)

---

## 迁移命令

### 基本命令

```bash
# 进入backend目录
cd backend

# 1. 创建新的迁移
python manage.py makemigrations

# 2. 查看待应用的迁移
python manage.py makemigrations [app_name]

# 3. 应用迁移到数据库
python manage.py migrate

# 4. 查看迁移状态
python manage.py showmigrations

# 5. 显示迁移SQL
python manage.py sqlmigrate [app_name] [migration_number]
```

### 高级命令

```bash
# 查看未应用的迁移
python manage.py showmigrations [app_name] --plan

# 伪造迁移(不修改数据库)
python manage.py migrate [app_name] [migration_number] --fake

# 撤销迁移(仅从迁移记录中删除,不修改数据库)
python manage.py migrate [app_name] [migration_number] --fake

# 生成迁移SQL但不执行
python manage.py sqlmigrate [app_name] [migration_number]

# 检测是否有模型变更但未创建迁移
python manage.py makemigrations --dry-run --verbosity 3
```

---

## 当前迁移历史

### apps/users

**初始迁移**: `0001_initial.py`

- Django默认User模型扩展
- 权限和组管理

### apps/projects

| 迁移文件 | 说明 |
|---------|------|
| `0001_initial.py` | 创建Project, ProjectStage, ProjectModelConfig模型 |
| `0002_project_jianying_draft_path.py` | 添加剪映草稿路径字段 |

### apps/prompts

| 迁移文件 | 说明 |
|---------|------|
| `0001_initial.py` | 创建PromptTemplateSet, PromptTemplate模型 |
| `0002_prompttemplate_model_provider.py` | 关联PromptTemplate到ModelProvider |
| `0003_globalvariable.py` | 创建GlobalVariable模型 |
| `0004_auto_20251215_1049.py` | 自动迁移 |
| `0005_create_mock_prompt_templates.py` | 创建Mock提示词模板数据 |

### apps/models

| 迁移文件 | 说明 |
|---------|------|
| `0001_initial.py` | 创建ModelProvider, ModelUsageLog模型 |
| `0002_auto_20251104_1015.py` | 自动迁移 |
| `0003_set_default_executors.py` | 设置默认AI服务提供商 |
| `0004_create_mock_providers.py` | 创建Mock提供商数据 |

### apps/content

| 迁移文件 | 说明 |
|---------|------|
| `0001_initial.py` | 创建ContentRewrite, Storyboard, GeneratedImage, GeneratedVideo, CameraMovement模型 |

---

## 执行迁移

### 首次部署

```bash
# 1. 应用所有迁移
python manage.py migrate

# 2. 创建超级用户
python manage.py createsuperuser

# 3. 验证迁移状态
python manage.py showmigrations
```

### 开发环境迁移

```bash
# 创建新迁移后立即应用
python manage.py makemigrations
python manage.py migrate
```

### 生产环境迁移

**⚠️ 重要: 生产环境迁移前务必备份！**

```bash
# 1. 备份数据库
pg_dump -U username -d dbname > backup_$(date +%Y%m%d).sql

# 2. 检查待应用的迁移
python manage.py showmigrations --plan

# 3. 模拟运行(显示SQL但不执行)
python manage.py sqlmigrate [app_name] [migration_number]

# 4. 应用迁移
python manage.py migrate

# 5. 验证数据完整性
python manage.py check
```

---

## 回滚迁移

### 查看迁移历史

```bash
# 显示所有迁移
python manage.py showmigrations

# 查看特定app的迁移
python manage.py showmigrations [app_name]
```

### 回滚到指定迁移

```bash
# 回滚到上一个迁移
python manage.py migrate [app_name] [previous_migration_name]

# 回滚到特定迁移
python manage.py migrate projects 0001_initial

# 回滚所有迁移(慎用!)
python manage.py migrate [app_name] zero
```

### 回滚示例

```bash
# 回滚projects应用到0002之前
python manage.py migrate projects 0001

# 回滚并重新应用
python manage.py migrate projects 0001
python manage.py migrate projects 0002
```

**⚠️ 注意**: 回滚会删除数据! 确保在执行前备份。

---

## 数据迁移vs结构迁移

### 结构迁移 (Schema Migrations)

- **用途**: 修改数据库结构(表、字段、索引)
- **命令**: `python manage.py makemigrations`
- **特点**: 自动检测模型变更

**示例**:
```python
# 修改模型后
class Project(models.Model):
    new_field = models.CharField(max_length=100)

# 创建迁移
python manage.py makemigrations
# 生成: 000X_add_new_field.py
```

### 数据迁移 (Data Migrations)

- **用途**: 迁移或转换现有数据
- **命令**: `python manage.py makemigrations --empty`
- **特点**: 需要手动编写迁移逻辑

**示例**:
```python
# 1. 创建空迁移
python manage.py makemigrations myapp --empty data_migration_name

# 2. 编辑生成的迁移文件
from django.db import migrations

def forward(apps, schema_editor):
    # 迁移逻辑
    MyModel.objects.filter(status='old').update(status='new')

def backward(apps, schema_editor):
    # 回滚逻辑
    MyModel.objects.filter(status='new').update(status='old')

# 3. 应用迁移
python manage.py migrate myapp
```

---

## 故障排查

### 常见问题

#### 1. 迁移冲突

**症状**: 多个开发者创建同名迁移导致冲突

**解决方案**:
```bash
# 方案A: 合并迁移
python manage.py makemigrations --merge

# 方案B: 删除冲突迁移重新创建
rm apps/*/migrations/0XXX_*.py
python manage.py makemigrations
```

#### 2. 迁移依赖循环

**症状**: `django.db.migrations.exceptions.InconsistentMigrationHistory`

**解决方案**:
```bash
# 1. 回滚到一致状态
python manage.py migrate [app_name] [consistent_migration]

# 2. 伪造迁移标记为已应用
python manage.py migrate [app_name] [migration_name] --fake

# 3. 重新应用
python manage.py migrate [app_name]
```

#### 3. 数据库锁定

**症状**: `database is locked` (SQLite)

**解决方案**:
```bash
# 关闭所有Django进程和管理命令
ps aux | grep python | grep manage.py

# 或使用SQLite检查
lsof | grep db.sqlite3
kill -9 [PID]
```

#### 4. 迁移文件缺失

**症状**: `No migration found for app`

**解决方案**:
```bash
# 1. 伪造初始迁移
python manage.py migrate --fake-initial

# 2. 伪造到特定迁移
python manage.py migrate [app_name] [migration_name] --fake
```

#### 5. 字段冲突

**症状**: `django.db.utils.OperationalError: duplicate column name`

**解决方案**:
```bash
# 1. 检查当前迁移状态
python manage.py showmigrations

# 2. 如果字段已存在，可以跳过此迁移
python manage.py migrate [app_name] --fake [migration_name]

# 3. 或删除冲突的迁移文件并重新创建
```

### 调试技巧

```bash
# 查看迁移SQL(不执行)
python manage.py sqlmigrate [app_name] [migration_number]

# 检查模型变更
python manage.py makemigrations --dry-run --verbosity 3

# 验证迁移状态
python manage.py showmigrations [app_name] --plan

# 测试迁移(使用测试数据库)
python manage.py migrate --settings=config.settings.test
```

---

## 最佳实践

### 迁移开发原则

1. **单一职责**: 每个迁移只做一件事
2. **向前兼容**: 迁移应该向前兼容，允许后续迁移依赖
3. **幂等性**: 迁移应该可以重复执行而不出错
4. **可逆性**: 迁移应该定义forward和backward方法

### 命名约定

- 迁移文件: `0001_description.py`, `0002_description.py`
- 数据迁移: 在名称中包含`data_migration`
- 自动迁移: `000X_auto_YYYYMMDD_HHMM.py`

### 开发流程

```bash
# 1. 修改模型
# apps/projects/models.py

# 2. 创建迁移
python manage.py makemigrations

# 3. 审查生成的迁移文件
# apps/projects/migrations/000X_auto_....py

# 4. 应用迁移
python manage.py migrate

# 5. 验证
python manage.py check
```

### 生产环境检查清单

- [ ] 备份数据库
- [ ] 检查待应用的迁移 (`showmigrations --plan`)
- [ ] 在测试环境验证迁移
- [ ] 准备回滚计划
- [ ] 通知团队成员
- [ ] 选择低峰时段执行
- [ ] 执行迁移
- [ ] 验证应用功能
- [ ] 监控错误日志

---

## 迁移脚本

### 快速初始化

```bash
#!/bin/bash
# backend/scripts/init_db.sh

echo "初始化数据库..."

# 应用所有迁移
python manage.py migrate --noinput

# 创建测试数据
python manage.py loaddata fixtures/*.json

# 创建超级用户(非交互)
echo "from django.contrib.auth import get_user_model; User = get_user_model(); User.objects.create_superuser('admin', 'admin@example.com', 'admin123')" | python manage.py shell

echo "数据库初始化完成!"
```

### 备份脚本

```bash
#!/bin/bash
# backend/scripts/backup_db.sh

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backups"
DB_NAME="ai_story"

# PostgreSQL备份
pg_dump -U $DB_USER -d $DB_NAME > "$BACKUP_DIR/backup_$DATE.sql"

# SQLite备份
cp db.sqlite3 "$BACKUP_DIR/db_backup_$DATE.sqlite3"

echo "数据库备份完成: backup_$DATE"
```

---

## 相关文档

- **Django官方文档**: [Migrations](https://docs.djangoproject.com/en/3.2/topics/migrations/)
- **项目README**: [backend/README.md](../README.md)
- **项目架构**: [CLAUDE.md](../CLAUDE.md)
- **剪映集成**: [JIANYING_QUICKSTART.md](./JIANYING_QUICKSTART.md)

---

## 迁移状态快照

**生成时间**: 2026-01-26

### 当前迁移状态

```
users
 [X] 0001_initial

projects
 [X] 0001_initial
 [X] 0002_project_jianying_draft_path

prompts
 [X] 0001_initial
 [X] 0002_prompttemplate_model_provider
 [X] 0003_globalvariable
 [X] 0004_auto_20251215_1049
 [X] 0005_create_mock_prompt_templates

models
 [X] 0001_initial
 [X] 0002_auto_20251104_1015
 [X] 0003_set_default_executors
 [X] 0004_create_mock_providers

content
 [X] 0001_initial
```

---

## 附录

### A. 迁移文件位置

```
backend/
├── apps/
│   ├── users/
│   │   └── migrations/
│   ├── projects/
│   │   └── migrations/
│   ├── prompts/
│   │   └── migrations/
│   ├── models/
│   │   └── migrations/
│   └── content/
│       └── migrations/
```

### B. 迁移相关配置

```python
# settings/base.py
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}
```

### C. 环境变量

```bash
# 开发环境
DATABASE_URL=sqlite:///db.sqlite3

# 生产环境
# DATABASE_URL=postgresql://user:password@localhost:5432/dbname
```

---

**文档维护**: 当添加新的迁移时，请更新本文档的"当前迁移历史"部分。
