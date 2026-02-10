# 文档编写和维护规范

> **版本**: v2.0 | **最后更新**: 2026-01-31 | **维护者**: AI Story Development Team

本文档定义了AI Story项目的文档编写和维护规范，确保项目文档始终保持清晰、一致、易于维护。

---

## 📋 目录

1. [文档组织原则](#文档组织原则)
2. [文档分类标准](#文档分类标准)
3. [新开发文档规范](#新开发文档规范)
4. [文档编写指南](#文档编写指南)
5. [文档更新流程](#文档更新流程)
6. [审查验收标准](#审查验收标准)

---

## 🎯 文档组织原则

### 核心原则

1. **受众优先** - 按读者角色组织，而非按技术结构
2. **任务驱动** - 文档应该帮助用户完成任务
3. **单一来源** - 避免重复内容，保持权威来源唯一
4. **渐进式披露** - 从概览到细节，让读者按需深入

### 目录结构

```
docs/                           # 唯一文档中心
├── index.md                    # 主导航（角色视图）
├── overview.md                 # 项目总览
├── QUICKSTART.md               # 快速开始
│
├── epic-1/ ~ epic-9/           # Epic文档（项目历史）
├── guides/                     # 操作指南（用户文档）
│   ├── deployment/             # 部署指南
│   ├── admin/                  # 管理员指南
│   └── troubleshooting/        # 故障排查
│
├── technical/                  # 技术参考（开发文档）
│   ├── api/                    # API文档
│   ├── logging/                # 日志系统
│   ├── monitoring/             # 监控系统
│   └── performance/            # 性能优化
│
├── testing/                    # 测试文档
│   ├── test-strategy.md        # 测试策略
│   ├── coverage-reports/       # 覆盖率报告
│   └── e2e-testing.md          # E2E测试
│
└── bmad/                       # BMad工作流产物
    ├── planning/               # 规划阶段
    ├── implementation/         # 实施阶段
    └── retrospectives/         # 回顾阶段
```

---

## 📂 文档分类标准

### 按文档类型分类

| 类型 | 位置 | 受众 | 示例 |
|------|------|------|------|
| **Epic文档** | `docs/epic-N/` | 所有角色 | Epic总结、Story文档、回顾文档 |
| **操作指南** | `docs/guides/` | 用户、运维 | 部署、管理、故障排查 |
| **技术参考** | `docs/technical/` | 开发者 | API、日志、监控、性能 |
| **测试文档** | `docs/testing/` | 测试工程师 | 测试策略、覆盖率、E2E |
| **工作流产物** | `docs/bmad/` | 项目经理 | PRD、架构、Story、回顾 |

### 按受众角色分类

| 角色 | 主要关注文档 | 次要文档 |
|------|-------------|---------|
| **👨‍💻 开发者** | technical/, testing/ | epic-*/, guides/ |
| **🔧 运维人员** | guides/deployment/, technical/monitoring/ | guides/troubleshooting/ |
| **🧪 测试工程师** | testing/, epic-1/ | guides/test-validation.md |
| **📋 产品经理** | epic-*/, bmad/planning/ | overview.md |

---

## 🆕 新开发文档规范

### 开始新Epic/Story时

#### 1. Epic规划阶段

**创建Epic目录**：
```bash
mkdir -p docs/epic-N
```

**创建Epic README骨架**：
```markdown
# Epic N: [Epic名称]

> **状态**: 🚧 In Progress | **开始时间**: YYYY-MM-DD

## 🎯 Epic概述
[业务背景和价值]

## 📊 Epic成果
[预期功能列表]

## 📚 文档链接
- [Story文档](stories/)
- [回顾文档](#) （Epic完成后创建）
```

**在docs/index.md中注册Epic**：
- 在"Epic文档导航"章节添加Epic条目
- 状态标记为"🚧 In Progress"

#### 2. Story开发阶段

**使用BMad工作流创建Story**：
```bash
# Story会自动创建在 _bmad-output/implementation-artifacts/
# Story完成后，复制到 docs/epic-N/stories/
```

**Story文档必须包含**：
- ✅ 用户故事（作为...我需要...以便...）
- ✅ 验收标准（AC ID: 具体可验证的标准）
- ✅ 实施记录（tasks/subtasks完成状态）
- ✅ 变更日志（日期、变更内容、作者）

#### 3. 测试阶段

**更新测试文档**：

1. **单元测试** - 在Story文档中记录
2. **集成测试** - 更新 `docs/testing/coverage-reports/`
3. **E2E测试** - 添加到 `docs/testing/e2e-testing.md`

**测试覆盖率报告**：
```bash
# 生成覆盖率报告
pytest --cov=apps/your_module --cov-report=html

# 复制到文档中心
cp htmlcov/ docs/testing/coverage-reports/your_module/
```

#### 4. 完成阶段

**创建Epic回顾文档**：
```bash
# 使用BMad retrospective工作流
# 文档保存在 docs/bmad/retrospectives/epic-N-retro-YYYY-MM-DD.md
```

**更新Epic README**：
- 状态改为"✅ Done"
- 添加完成时间和测试覆盖率
- 补充"经验教训"章节

**更新docs/index.md**：
- Epic状态改为"✅ 完成"
- 添加测试覆盖率数据

---

## ✍️ 文档编写指南

### Markdown规范

#### 1. 文档结构

```markdown
# 文档标题

> **状态**: 状态标识 | **最后更新**: YYYY-MM-DD | **维护者**: 姓名

## 目录
[如果文档较长，添加目录]

## 章节1
[内容]

## 章节2
[内容]

---
**最后更新**: YYYY-MM-DD
```

#### 2. 标题层级

- `#` 一级标题：文档标题（每个文件只有1个）
- `##` 二级标题：主要章节
- `###` 三级标题：子章节
- `####` 四级标题：细节内容

**不要跳级**（如从##直接跳到####）

#### 3. 链接规范

**相对链接**（优先使用）：
```markdown
[文档标题](../path/to/file.md)
[章节标题](./file.md#anchor-id)
```

**绝对链接**（仅用于外部资源）：
```markdown
[ Django文档](https://docs.djangoproject.com/)
```

#### 4. 代码块

**带语言标识**：
````markdown
```python
def hello():
    print("Hello, World!")
```
````

**带文件路径**（可选）：
````markdown
```python path="backend/apps/projects/views.py"
def hello():
    print("Hello, World!")
```
````

#### 5. 列表

**无序列表**：
```markdown
- 项目1
- 项目2
  - 子项目2.1
  - 子项目2.2
```

**有序列表**：
```markdown
1. 步骤1
2. 步骤2
3. 步骤3
```

**任务列表**：
```markdown
- [x] 已完成任务
- [ ] 未完成任务
```

#### 6. 表格

```markdown
| 列1 | 列2 | 列3 |
|-----|-----|-----|
| 数据1 | 数据2 | 数据3 |
```

#### 7. 引用和提示

**信息提示**：
```markdown
> **提示**: 这是有用的提示信息
```

**警告**：
```markdown
> ⚠️ **注意**: 这是需要特别注意的内容
```

**错误标识**：
```markdown
> ❌ **错误**: 这个操作会导致错误
```

---

## 🔄 文档更新流程

### 何时更新文档

| 场景 | 更新内容 | 负责人 |
|------|---------|--------|
| **新功能开发** | 创建Epic/Story文档 | 开发者 + PM |
| **API变更** | 更新technical/api/ | 开发者 |
| **配置变更** | 更新guides/deployment/ | 运维 + 开发者 |
| **Bug修复** | 更新guides/troubleshooting/ | 开发者 |
| **测试完成** | 更新testing/coverage-reports/ | 测试工程师 |
| **Epic完成** | 创建回顾文档 | 团队 |

### 文档更新步骤

1. **定位文档**
   - 使用 `docs/index.md` 找到正确的文档位置
   - 如果是新类型文档，先确认应该放在哪里

2. **更新文档**
   - 遵循Markdown规范
   - 保持文档风格一致
   - 更新"最后更新"时间戳

3. **更新索引**
   - 如果创建了新文档，在相关索引中添加链接
   - 更新docs/index.md（如果影响导航）

4. **验证链接**
   ```bash
   # 检查Markdown链接是否有效
   find docs/ -name "*.md" -exec grep -l "\[.*\](.*\.md)" {} \;
   ```

5. **提交审查**
   - 提交PR时包含文档变更
   - 代码审查时一并审查文档

---

## ✅ 审查验收标准

### 文档质量检查清单

#### 内容完整性
- [ ] 文档有明确的标题和描述
- [ ] 包含"最后更新"时间戳
- [ ] 所有链接有效（无404）
- [ ] 代码示例可运行
- [ ] 截图清晰（如果包含）

#### 结构一致性
- [ ] 遵循Markdown规范
- [ ] 标题层级不跳级
- [ ] 列表格式统一
- [ ] 代码块带语言标识

#### 受众适配
- [ ] 技术深度适合目标受众
- [ ] 提供必要的背景信息
- [ ] 包含实际使用示例
- [ ] 避免未解释的术语

#### 可维护性
- [ ] 避免重复内容（单一来源）
- [ ] 相关文档有交叉引用
- [ ] 使用相对链接（非外部链接）
- [ ] 文档位置符合分类标准

### 常见问题❌

| 问题 | 示例 | 正确做法✅ |
|------|------|----------|
| **链接失效** | `[文档](../old-path/file.md)` | 使用docs/index.md定位正确路径 |
| **重复内容** | 同一API文档在2个位置 | 保留1个权威来源，其他用链接引用 |
| **过时内容** | 最后更新: 2025-01-01 | 每次更新都修改时间戳 |
| **无受众定位** | 技术文档混杂操作指南 | 按受众分类到technical/或guides/ |
| **缺少上下文** | "配置如下："然后是代码 | 先说明为什么需要配置，再给出代码 |

---

## 📊 文档维护最佳实践

### 日常维护

1. **代码变更同步更新文档**
   - API变更 → 更新technical/api/
   - 配置变更 → 更新guides/deployment/
   - 新功能 → 更新相关Epic文档

2. **定期审查**
   - 每个Epic完成后审查文档完整性
   - 每月检查一次链接有效性
   - 每季度审查文档准确性

3. **持续改进**
   - 收集用户反馈
   - 优化文档结构
   - 补充缺失的文档

### 文档生命周期

```
创建 → 维护 → 归档
  ↓      ↓       ↓
活跃   定期   历史参考
文档   更新   (archive/)
```

**活跃文档** - `docs/`
- 持续更新，与代码同步
- 遵循本文档规范

**归档文档** - `archive/`
- 只读，不修改
- 保留历史价值

---

## 🆘 获取帮助

### 文档问题排查

**找不到文档？**
1. 查看 [docs/index.md](../index.md) - 主导航
2. 使用 `grep -r "关键词" docs/` - 搜索文档内容
3. 检查是否已归档到 `archive/`

**链接失效？**
1. 检查相对路径是否正确
2. 确认目标文件是否存在
3. 查看 [archive/README.md](../archive/README.md) - 可能已归档

**不知道文档该放哪？**
1. 参考本文档的"文档分类标准"
2. 查找类似内容的现有文档位置
3. 咨询团队成员

---

## 📚 相关文档

- [文档中心索引](../index.md) - 所有文档的导航入口
- [项目总览](../overview.md) - 项目当前状态
- [快速开始](../QUICKSTART.md) - 5分钟上手
- [BMad工作流](./bmad/) - AI辅助开发方法论

---

**文档规范版本**: v2.0
**最后更新**: 2026-01-31
**维护团队**: AI Story Development Team
**下次审查**: 2026-04-30（每季度审查）
