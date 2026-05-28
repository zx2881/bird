# 全球鸟类分布与生物多样性保护知识图谱

基于 CSV 主数据源 + 静态分片 + 前端按需加载的鸟类知识图谱可视化项目。

## 技术栈

| 层 | 技术 |
|---|---|
| 前端 | Vue 3 + Vite + Element Plus + Pinia |
| 图谱 | 3d-force-graph + three.js (WebGL 3D) |
| 地图 | Leaflet |
| 数据构建 | Python 脚本 (CSV → 静态 JSON 分片) |

## 快速开始

```bash
npm install          # 安装前端依赖
npm run build:data   # 从 CSV 构建前端数据
npm run dev          # 启动开发服务器
```

### 本地 Neo4j 模式

数据量较大时，推荐开发阶段使用本地 Neo4j 承载图查询，CSV 仍然是主数据源。

```bash
copy .env.example .env
npm run neo4j:up
npm run import:neo4j
npm run dev:api
npm run dev
```

浏览器访问 `http://localhost:5173`。Neo4j Browser 在 `http://localhost:7474`，默认账号密码见 `.env.example`。

## 项目结构

```
├── data/                    # 主数据源 (CSV)
│   ├── birds.csv            # 鸟类实体
│   ├── locations.csv        # 地点实体
│   └── relations.csv        # 三元组关系
├── scripts/                 # Python 数据脚本
│   ├── build_knowledge_json.py    # 核心构建脚本
│   ├── crawl_from_wikipedia.py    # Wikipedia 抓取
│   ├── fetch_taxonomy.py          # Wikidata 分类标签
│   ├── fetch_bird_images.py       # 鸟类图片获取
│   ├── download_bird_name_list.py # AviList 鸟名下载
│   ├── backfill_taxonomy_from_avilist.py # 分类快速回填
│   ├── import_to_neo4j.py         # 导入本地 Neo4j
│   └── validate_data.py           # 数据校验
├── server/
│   └── neo4j-api.js         # 本地 Neo4j 查询 API
├── public/data/             # 构建产物 (自动生成，勿手动修改)
│   ├── summary.json         # 轻量索引
│   ├── graph_preview.json   # 首页预览图
│   ├── taxonomy_skeleton.json # 分类骨架
│   └── nodes/*.json         # 各节点详情切片
├── src/                     # Vue 3 前端
│   ├── App.vue
│   ├── views/
│   ├── stores/
│   ├── graph/
│   └── components/
└── public/knowledge.json    # 旧单体产物 (已废弃)
```

## 数据架构

维护 CSV (主数据源) → 运行构建脚本 → 自动生成 `public/data/*` 静态分片 → 前端按需加载。

本地 Neo4j 模式下，仍然维护 CSV；执行 `npm run import:neo4j` 后，前端通过 `server/neo4j-api.js` 按需查询 Neo4j。

- **首屏**: 只加载 `summary.json` + `graph_preview.json`，响应轻快
- **详情**: 点击节点时按需拉取 `nodes/[id].json`
- **图谱**: 预计算坐标 + 静止常态，拖拽时局部唤醒，不持续计算
- **部署**: 可选纯静态分片，或本地/服务器 Neo4j + API

## CSV 字段说明

### `data/birds.csv`

| 字段 | 说明 | 必填 |
|---|---|---|
| `id` | 唯一标识，如 `bird-siberian-crane` | ✓ |
| `name` | 中文名 | ✓ |
| `english_name` | 英文名 | ✓ |
| `latin_name` | 拉丁学名 | |
| `summary` | 简介 | |
| `lat` / `lng` | 代表坐标 | |
| `image_url` | 图片 URL (脚本自动填充) | |
| `order` / `family` / `genus` / `species` | 分类学名 (脚本自动填充) | |
| `order_cn` / `family_cn` / `genus_cn` / `species_cn` | 中文分类名 | |

### `data/locations.csv`

| 字段 | 说明 | 必填 |
|---|---|---|
| `id` | 唯一标识，如 `loc-poyang-lake` | ✓ |
| `name` | 地点名称 | ✓ |
| `summary` | 简介 | |
| `lat` / `lng` | 经纬度 | ✓ |

### `data/relations.csv`

| 字段 | 说明 | 必填 |
|---|---|---|
| `subject_id` / `object_id` | 主语/宾语实体 ID | ✓ |
| `subject` / `object` | 主语/宾语名称 | ✓ |
| `predicate` | 关系类型 | ✓ |
| `subject_type` / `object_type` | 主语/宾语类型 (Bird/Location/Habitat/Status/Threat) | ✓ |
| `evidence` | 证据文本 | |
| `object_summary` | 宾语节点补充说明 | |

支持的关系类型: `distributed_in` | `lives_in` | `has_status` | `threatened_by` | `belongs_to`

## 命令行参考

### 前端

```bash
npm install            # 安装依赖
npm run dev            # 开发服务器
npm run build          # 生产打包
npm run preview        # 预览打包结果
```

### 数据构建

```bash
npm run build:data     # 从 CSV 生成静态分片
npm run validate       # 数据校验
```

### Neo4j 本地开发

```bash
npm run neo4j:up       # 启动本地 Neo4j Docker 容器
npm run import:neo4j   # 清空并重新导入 CSV 构建出的图数据
npm run dev:api        # 启动本地查询 API，默认 http://localhost:5174
npm run neo4j:down     # 停止 Neo4j 容器
```

团队成员拉取代码后复制 `.env.example` 为 `.env`，再按上面的命令启动即可。`.env` 不提交到 Git。

### 数据采集 (包名对应 package.json scripts)

```bash
npm run download:bird-names                           # 下载 AviList 鸟名列表
npm run crawl:wikipedia -- --titles "Red-crowned Crane" # 抓取指定鸟类
python scripts/crawl_from_wikipedia.py --input-file data/bird_titles.csv  # 批量抓取
npm run fetch:bird-images                             # 批量获取图片
npm run fetch:taxonomy                                # 获取分类标签
python scripts/backfill_taxonomy_from_avilist.py      # AviList 快速回填
```

### 带代理

```bash
python scripts/crawl_from_wikipedia.py --input-file data/bird_titles.csv --proxy http://127.0.0.1:7890
python scripts/fetch_taxonomy.py --proxy http://127.0.0.1:7890
python scripts/fetch_bird_images.py --proxy http://127.0.0.1:7890
```

## 完整数据采集流程 (按顺序执行)

```bash
# 1. 下载 AviList 官方鸟名
npm run download:bird-names

# 2. Wikipedia 批量抓取 (耗时最长)
python scripts/crawl_from_wikipedia.py --input-file data/bird_titles.csv

# 3. AviList 快速回填 order/family (几秒)
python scripts/backfill_taxonomy_from_avilist.py

# 4. Wikidata 补中文分类名
npm run fetch:taxonomy

# 5. 批量获取鸟图
npm run fetch:bird-images

# 6. 数据校验
npm run validate

# 7. 生成前端数据
npm run build:data

# 8. 启动预览
npm run dev
```

**注意**: 不要同时运行多个写 CSV 的脚本，后写入会覆盖先写入的数据。

## 脚本说明

### `build_knowledge_json.py`
核心构建入口。读取三张 CSV → 验证数据一致性 → 生成 `public/data/` 下所有静态分片文件。**任何 CSV 修改后必须运行此脚本。**

### `import_to_neo4j.py`
复用构建脚本生成的完整图数据，写入本地 Neo4j。默认会先清空 Neo4j 当前图数据；如果需要增量 MERGE，可使用 `python scripts/import_to_neo4j.py --no-reset`。

### `crawl_from_wikipedia.py`
调用 MediaWiki API 抓取英文 Wikipedia 鸟类页面，自动抽取中文标题、摘要、分布/栖息/保护等关系字段，并写回 CSV。支持断点续跑 (`--input-file` + checkpoint)。

### `fetch_taxonomy.py`
通过 Wikidata API 获取鸟类的目/科/属/种英文与中文名称，回填 `birds.csv`。支持断点续跑，已有数据的自动跳过。

### `backfill_taxonomy_from_avilist.py`
从本地 `bird_titles.csv` 按英文名匹配，批量回填 order/family，无需联网，几秒完成。覆盖约 98%+ 鸟类。

### `fetch_bird_images.py`
通过 Wikipedia `prop=pageimages` API 批量获取鸟类题图 URL，仅处理 `image_url` 为空的记录。

### `download_bird_name_list.py`
从 AviList 官方下载标准鸟类名录，输出 `bird_titles.csv` 供后续抓取使用。

### `validate_data.py`
校验 `birds.csv`、`locations.csv`、`relations.csv` 之间的实体引用一致性。

### GBIF / 中国观鸟记录中心坐标获取
根目录下的 `gbif_coord_fetcher.py` 和 `china_bird_coord_fetcher.py` 用于补全鸟类坐标。

```bash
python gbif_coord_fetcher.py --null-only        # GBIF 补坐标
python china_bird_coord_fetcher.py --token YOUR_TOKEN --null-only  # 中国观鸟中心
```

## 前端架构

| 文件 | 职责 |
|---|---|
| `src/stores/graphStore.js` | 管理图数据状态，按需加载分片，增量合并节点/边 |
| `src/graph/SigmaCanvas.vue` | WebGL 3D 图谱渲染，预计算坐标 + 局部唤醒模式 |
| `src/views/Home.vue` | 首页：加载预览图 → 搜索/点击交互 |
| `src/views/BirdDetail.vue` | 详情页：按需拉取切片 → 渲染详情 + 地图 |

图谱渲染采用"静态坐标 + 拖拽瞬时唤醒"模式：常态静止零算力，拖拽时仅局部邻域临时参与模拟，松手后自动回锚到预计算坐标。

## 部署

项目支持两种部署方式。

### 纯静态部署

适合 GitHub Pages 等静态站点。

```bash
npm run build:data   # 生成数据
npm run build        # 打包前端，产物在 dist/
```

将 `dist/` 上传到静态服务器即可。PWA 使用 Workbox 运行时缓存 `/data/*.json`，不预缓存大量节点切片。

### Neo4j + API 部署

适合数据量更大、需要后端按需查询的环境。部署时需要同时运行 Neo4j、`server/neo4j-api.js` 和前端，并把 `VITE_API_BASE_URL` 指向 API 地址。

## 数据维护习惯

- 鸟类信息 → `birds.csv`
- 地点信息 → `locations.csv`
- 事实关系 → `relations.csv`（保留 `evidence` 用于人工审核）
- 同一个实体始终使用同一个 `id` 和标准名称
- 静态模式：任何 CSV 修改后执行 `npm run build:data`
- Neo4j 模式：任何 CSV 修改后执行 `npm run import:neo4j`

常见坑位：同一地点写多个名字、同一 `id` 对应多个名称、关系引用了不存在的地点/鸟类。

## 构建规模参考

当前示例数据集 (约 2000+ 节点切片):

| 文件 | 大小 |
|---|---|
| `summary.json` | ~194 KB |
| `graph_preview.json` | ~200 KB |
| 单个 `nodes/[id].json` | 平均 ~5 KB |

