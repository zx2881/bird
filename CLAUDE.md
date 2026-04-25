# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概览

这是一个“数据构建 + 前端可视化”的鸟类知识图谱项目：

- 主数据源是 `data/*.csv`（不是 `public/knowledge.json`）
- 前端 `src/App.vue` 只读取 `public/knowledge.json` 渲染图谱与地图
- Python 脚本负责从多来源增量整理 CSV，并构建 JSON

## 常用命令

### 前端开发

```bash
npm install
npm run dev
```

- Vite dev server 默认 `5173`

### 构建前端数据（核心）

```bash
npm run build:data
```

等价于：

```bash
python scripts/build_knowledge_json.py
```

用途：读取 `data/birds.csv`、`data/locations.csv`、`data/relations.csv`，输出 `public/knowledge.json`。

### 抓取与批量补数

```bash
npm run download:bird-names
npm run crawl:wikipedia -- --titles "Red-crowned Crane" --build-json
```

也可直接跑 Python：

```bash
python scripts/download_bird_name_list.py --output data/bird_titles.csv
python scripts/crawl_from_wikipedia.py --input-file data/bird_titles.csv --build-json
```

### 打包与预览

```bash
npm run build
npm run preview
```

## 数据与构建架构

### 1) 数据分层

- `data/birds.csv`：Bird 实体主表
- `data/locations.csv`：Location 实体主表
- `data/relations.csv`：事实关系主表（三元组 + 工程字段）
- `public/knowledge.json`：前端消费产物（构建输出，非主数据）

修改数据后，先运行 `npm run build:data`，再看前端效果。

### 2) 关系 Schema 与前端类型映射

`relations.csv` 支持关系：

- `distributed_in`
- `lives_in`
- `has_status`
- `threatened_by`
- `belongs_to`

`build_knowledge_json.py` 会把 `object_type` 映射到前端节点类型：

- Bird → `bird`
- Location → `location`
- Habitat → `habitat`
- Status → `status`
- Threat → `threat`
- Taxon → `taxonomy`

如果使用 `belongs_to`，`object_type` 应写 `Taxon`，前端才会稳定显示分类节点。

### 3) 构建脚本关键行为（`scripts/build_knowledge_json.py`）

- 严格校验 CSV 列、关系类型、实体可解析性
- 先创建 Bird/Location 节点，再从关系自动创建 Habitat/Status/Threat/Taxon 节点
- 聚合每只鸟的 `locations/habitats/threats/status`
- Bird 坐标缺失时，尝试用首个分布地点坐标补齐
- 生成 `meta + nodes + links` JSON 结构

这意味着：数据一致性问题优先在构建阶段暴露，不要等前端渲染报错。

### 4) Wikipedia 增量管线（`scripts/crawl_from_wikipedia.py`）

该脚本会同时维护：

- `data/birds.csv`
- `data/locations.csv`
- `data/relations.csv`
- `data/wikipedia_raw/*.json`
- `data/wikipedia_checkpoint/*.json`

关键点：

- 支持断点续跑，已完成标题会自动跳过
- 每个标题处理后立刻落盘 CSV + checkpoint
- 可用 `--overwrite` 强制重抓并覆盖同 id 非空字段
- `--build-json` 会在末尾自动调用 `build_knowledge_json.py`

## 前端运行关系

### 前端（`src/App.vue`）

- 仅 `fetch('/knowledge.json')`
- 用 ECharts force graph + Leaflet 地图联动
- 图谱有概览/聚焦模式、节点密度与标签策略控制
- 点击节点会驱动侧栏详情与地图定位

## 协作注意点

- 不要长期手改 `public/knowledge.json`；应改 `data/*.csv` 或脚本来源，再重建
- 任何数据维护任务，优先确认 `relations.csv` 的 `subject_id/object_id` 稳定且与名称一致
- 本项目无内置 lint/test 脚本；验证变更通常依赖：
  1) `npm run build:data` 成功
  2) `npm run dev` 下功能手测
