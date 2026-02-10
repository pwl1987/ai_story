# 历史文档归档

> 本目录包含项目演进过程中的历史文档，仅用于参考，不作为当前文档使用。

---

## 📋 归档说明

**归档日期**: 2026-01-31
**归档原因**: 文档重组 - 将历史文档与活跃文档分离，提高文档可维护性

---

## 🗂️ 归档目录结构

### day-reports/
**内容**: 项目初期的每日执行记录和总结（Day 1-7）

**说明**: 这些文档记录了项目早期的执行过程，现已整合到各自的Epic文档中。

**历史价值**:
- 记录了项目初期的决策过程
- 展示了团队的执行节奏
- 包含有价值的问题排查记录

**当前替代文档**: [docs/epic-*/README.md](../docs/)

### legacy-docs/
**内容**: 早期版本的各种报告和指南

**说明**: 这些是项目演进过程中的早期文档，已被更新的版本替代。

**包含内容**:
- 早期架构文档
- 旧版配置指南
- 过时的技术方案

**当前替代文档**: [docs/](../docs/)

### _bmad-output-legacy-backend/
**内容**: backend/_bmad-output/的历史备份（2026-01-27之前）

**说明**: backend目录下的BMad工作流产物，包含规划文档和演示文稿。

**包含内容**:
- `planning-artifacts/` - 早期的项目规划产物
  - week-2-final-summary.md
  - phase-1-3-final-summary.md
  - code-quality-review-plan.md
  - 等等...
- `presentations/` - 项目演示文稿
  - project-summary-slides.md

**当前替代文档**:
- [docs/bmad/planning/](../docs/bmad/planning/) - 当前规划文档
- [docs/bmad/implementation/](../docs/bmad/implementation/) - 当前实施文档

---

## 🔍 查找历史文档

如果您需要查找历史文档：

1. **按日期查找**: 检查文档的创建/修改日期
2. **按关键词搜索**: 使用 `grep -r "关键词" archive/`
3. **按类型查找**:
   - 项目初期记录 → `day-reports/`
   - 早期版本文档 → `legacy-docs/`
   - BMad产物 → `_bmad-output-legacy-backend/`

---

## ⚠️ 重要提示

### 不要修改归档文档

归档文档是历史记录，**不应被修改或删除**。它们保留了项目演进的历史轨迹，对于：
- 理解项目历史决策
- 追溯需求变更过程
- 学习团队演进经验

都有重要价值。

### 需要更新内容？

如果您发现归档文档中的内容需要更新：
1. 在 `docs/` 目录创建或更新相应文档
2. 在归档文档中添加引用指向新文档
3. 保持归档文档的原始状态

---

## 📊 归档统计

| 目录 | 文档数 | 最后更新 | 状态 |
|------|--------|----------|------|
| day-reports/ | 7个报告 | 2026-01-25 | 📦 已归档 |
| legacy-docs/ | 20+个文档 | 2026-01-26 | 📦 已归档 |
| _bmad-output-legacy-backend/ | 17个文档 | 2026-01-27 | 📦 已归档 |

---

## 🔗 相关文档

- [文档中心](../docs/index.md) - 当前活跃文档
- [项目总览](../docs/overview.md) - 项目当前状态
- [Epic文档](../docs/epic-*/README.md) - 各Epic的完整总结

---

**归档维护**: AI Story Development Team
**最后更新**: 2026-01-31
