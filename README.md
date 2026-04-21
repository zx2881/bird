# 全球鸟类分布与生物多样性保护知识图谱构建

本项目现在采用两层数据结构：

- `data/*.csv` 是长期维护的主数据源
- `public/knowledge.json` 是给前端直接读取的生成结果

这样做的目的很直接：后续你只维护表格，不再手改大 JSON。

## 1. 当前项目包含什么

- `Vue 3 + Vite + Element Plus` 前端单页应用
- `ECharts` 力导向知识图谱与 `Leaflet` 地图联动
- `data/` 目录下的 CSV 填表模式主数据源
- `scripts/build_knowledge_json.py` 数据整合脚本
- `scripts/download_bird_name_list.py` 的 AviList 标准鸟名下载脚本
- `scripts/crawl_from_wikipedia.py` 的 Wikipedia 批量抓取脚本
- `server/` 下的 Node 简易三元组测试接口
- `scripts/fetch_gbif_data.py` 的 GBIF 分布抓取示例

## 2. 目录结构

```text
.
├─ data/
│  ├─ birds.csv
│  ├─ locations.csv
│  └─ relations.csv
├─ public/
│  └─ knowledge.json
├─ scripts/
│  ├─ build_knowledge_json.py
│  ├─ crawl_from_wikipedia.py
│  ├─ download_bird_name_list.py
│  └─ fetch_gbif_data.py
├─ server/
│  ├─ data/
│  │  └─ sample-docs.json
│  ├─ services/
│  │  └─ tripleExtractor.js
│  └─ index.js
├─ src/
│  ├─ App.vue
│  ├─ main.js
│  └─ style.css
├─ index.html
├─ package.json
└─ vite.config.js
```

## 3. 填表模式怎么工作

现在的数据流是：

1. 你维护 `data/birds.csv`
2. 你维护 `data/locations.csv`
3. 你维护 `data/relations.csv`
4. 运行 `python scripts/build_knowledge_json.py`
5. 自动生成前端读取的 `public/knowledge.json`

也就是：

- 表格是“主数据”
- JSON 是“构建产物”

## 4. 三个 CSV 文件怎么填

### `data/birds.csv`

作用：

- 存鸟类实体本身的信息
- 一行对应一个 Bird 节点

列说明：

- `id`: 鸟类唯一标识，建议固定不改，例如 `bird-red-crowned-crane`
- `name`: 中文名
- `english_name`: 英文名
- `latin_name`: 拉丁学名
- `summary`: 鸟类简介
- `lat`: 鸟类代表坐标纬度
- `lng`: 鸟类代表坐标经度

示例：

```csv
id,name,english_name,latin_name,summary,lat,lng
bird-siberian-crane,白鹤,Siberian Crane,Leucogeranus leucogeranus,大型涉禽，依赖湿地和浅水湖泊。,29.103,116.221
```

说明：

- `birds.csv` 只保存鸟类本身信息
- `status`、`habitats`、`threats`、`locations` 不直接写在这里
- 这些字段会由 `relations.csv` 自动聚合出来

### `data/locations.csv`

作用：

- 存地点实体信息
- 一行对应一个 Location 节点

列说明：

- `id`: 地点唯一标识，例如 `loc-poyang-lake`
- `name`: 地点名称
- `summary`: 地点简介
- `lat`: 纬度
- `lng`: 经度

示例：

```csv
id,name,summary,lat,lng
loc-poyang-lake,鄱阳湖,中国重要候鸟越冬地。,29.103,116.221
```

说明：

- 地图联动依赖 `locations.csv` 的经纬度
- 同一个地点必须复用同一个 `id`
- 不要同时出现“鄱阳湖”“江西鄱阳湖”“Poyang Lake”三个重复节点

### `data/relations.csv`

作用：

- 存三元组关系
- 一行对应一个事实
- 这是最接近 [三元组提取.md](C:/Users/29802/Documents/全球鸟类分布与生物多样性保护知识图谱构建/三元组提取.md) 的主表

列说明：

- `subject_id`: 主语实体 id，工程字段，方便稳定构图
- `subject`: 主语实体名
- `predicate`: 关系类型
- `object_id`: 宾语实体 id，工程字段，方便稳定构图
- `object`: 宾语实体名
- `subject_type`: 主语类型
- `object_type`: 宾语类型
- `evidence`: 证据语句
- `object_summary`: 可选，用于给自动生成的宾语节点补简介

示例：

```csv
subject_id,subject,predicate,object_id,object,subject_type,object_type,evidence,object_summary
bird-siberian-crane,白鹤,distributed_in,loc-poyang-lake,鄱阳湖,Bird,Location,白鹤主要分布于鄱阳湖。,
bird-siberian-crane,白鹤,lives_in,hab-wetland,湿地,Bird,Habitat,白鹤栖息于湿地。,浅水、沼泽与植被斑块组成的高生产力生态系统。
bird-siberian-crane,白鹤,has_status,status-cr,CR,Bird,Status,白鹤的保护等级为 CR。,IUCN 极危。
bird-siberian-crane,白鹤,threatened_by,threat-climate-change,气候变化,Bird,Threat,白鹤面临气候变化威胁。,长期改变水文节律与生态系统稳定性的全球变化因素。
```

### `relations.csv` 与 `三元组提取.md` 的关系

这张表保留了原始 Schema 里的核心字段：

- `subject`
- `predicate`
- `object`
- `subject_type`
- `object_type`
- `evidence`

另外我补了 3 个工程字段：

- `subject_id`
- `object_id`
- `object_summary`

原因很明确：

- 前端画图必须依赖稳定 `id`
- 只靠中文名称连接节点，后期很容易重名或改名
- `object_summary` 让你在不新增第四张表的前提下，也能给 Habitat/Status/Threat 节点补说明

## 5. 目前支持的关系类型

`relations.csv` 里当前支持：

- `distributed_in`
- `lives_in`
- `has_status`
- `threatened_by`
- `belongs_to`

其中前四种已经在样例数据中使用。

关于 `belongs_to`：

- 原始 `三元组提取.md` 里定义了 `belongs_to`
- 但实体类型里没有单独给“科/目”定义类型
- 这是原始 Schema 的一个空缺

这里我做了一个工程性补充：

- 如果你后续要使用 `belongs_to`
- 建议在 `relations.csv` 中把 `object_type` 写成 `Taxon`
- 构建脚本会把它映射成前端里的 `taxonomy` 节点

这个补充是为了让前端图谱能够稳定渲染分类单元。

## 6. 构建脚本说明

### `scripts/build_knowledge_json.py`

作用：

- 读取 `data/birds.csv`
- 读取 `data/locations.csv`
- 读取 `data/relations.csv`
- 验证关系、实体和名称是否一致
- 自动生成 `public/knowledge.json`

脚本主要做了 5 件事：

1. 读取三张 CSV
2. 先创建 Bird 和 Location 节点
3. 再从 `relations.csv` 自动创建 Habitat / Status / Threat / Taxon 节点
4. 自动为每只鸟聚合出：
   - `locations`
   - `habitats`
   - `threats`
   - `status`
5. 输出前端需要的 `nodes + links` 结构

### 为什么这个脚本很重要

因为它会帮你提前发现填表错误，例如：

- 同一个 `object_id` 对应两个不同名称
- `relations.csv` 里写了一个不存在的地点
- `subject` 名称和 `birds.csv` 对不上
- `predicate` 写错

这种错误如果等到前端报错再查，会很慢；现在在构建阶段就能直接发现。

## 7. 现有前端代码怎么配合这个模式

### `src/App.vue`

作用：

- 仍然只读取 `public/knowledge.json`
- 不直接读取 CSV
- 所以你后面无需改动前端主逻辑，只需要先跑构建脚本

当前页面功能不变：

- 左侧搜索和实体详情
- 右侧知识图谱与地图联动
- 点击鸟类看详情
- 点击地点跳地图
- 点击测试按钮调用后端三元组接口

另外我补上了 `taxonomy` 类型兼容，避免以后启用 `belongs_to` 时再返工。

### `public/knowledge.json`

现在它不再是“主数据源”，而是“自动生成文件”。

你后面应该：

- 改 `data/*.csv`
- 运行构建脚本
- 让脚本覆盖 `public/knowledge.json`

不建议长期手动编辑这个文件。

## 8. 命令怎么用

安装前端依赖：

```bash
npm install
```

从 CSV 生成前端数据：

```bash
npm run build:data
```

启动后端测试服务：

```bash
npm run server
```

启动前端：

```bash
npm run dev
```

生产打包：

```bash
npm run build
```

抓取 Wikipedia 并写入 `data/*.csv`：

```bash
npm run crawl:wikipedia -- --titles "Red-crowned Crane" "Crested Ibis" --build-json
```

下载 AviList 标准鸟名并生成 `bird_titles.csv`：

```bash
npm run download:bird-names
```

也可以指定输出路径：

```bash
python scripts/download_bird_name_list.py --output data/bird_titles.csv
```

也可以直接运行 Python：

```bash
python scripts/crawl_from_wikipedia.py --titles "California Condor" "Philippine Eagle" --build-json
```

推荐日常顺序：

```bash
npm run build:data
npm run dev
```

如果你修改了 `data/*.csv`，就重新执行一次：

```bash
npm run build:data
```

如果你是从 Wikipedia 新抓数据，建议直接执行：

```bash
npm run crawl:wikipedia -- --titles "Red-crowned Crane" --build-json
```

如果你要先批量准备标准鸟名，再喂给 Wikipedia 爬虫，建议顺序是：

```bash
npm run download:bird-names
python scripts/crawl_from_wikipedia.py --input-file data/bird_titles.csv --build-json
```

脚本会同时写入：

- `data/birds.csv`
- `data/locations.csv`
- `data/relations.csv`
- `data/wikipedia_raw/*.json`

## 9. 现在这三张表里已经放了什么

目前样例数据已经迁移进 `data/`：

- `birds.csv`: 10 种代表性鸟类
- `locations.csv`: 10 个代表性地点
- `relations.csv`: 74 条关系事实

构建后，前端读取的 [public/knowledge.json](C:/Users/29802/Documents/全球鸟类分布与生物多样性保护知识图谱构建/public/knowledge.json) 会自动包含：

- Bird 节点
- Location 节点
- Habitat 节点
- Status 节点
- Threat 节点
- 关系线 `links`

## 10. 后端测试部分说明

### `server/data/sample-docs.json`

作用：

- 存放从公开资料整理的少量测试文本
- 用于演示三元组抽取，不作为前端主数据源

### `server/services/tripleExtractor.js`

作用：

- 根据 [三元组提取.md](C:/Users/29802/Documents/全球鸟类分布与生物多样性保护知识图谱构建/三元组提取.md) 的 Schema 抽取规则化三元组

这一层和 `data/*.csv` 的关系是：

- `sample-docs.json` 更接近原始文本
- `relations.csv` 更接近人工审核后的结构化主数据

实际工作流建议是：

1. 从资料收集原文
2. 先抽取三元组
3. 人工审核
4. 再写入 `relations.csv`
5. 最后生成前端 JSON

## 11. GBIF 脚本说明

### `scripts/fetch_gbif_data.py`

作用：

- 从 GBIF 抓带坐标的 occurrence 记录
- 演示如何把外部分布点转成前端兼容数据

它和填表模式的关系是：

- 你可以先用它抓到分布点
- 再把整理后的结果写回 `locations.csv` 和 `relations.csv`
- 最后统一由 `build_knowledge_json.py` 出图谱

所以长远看，`fetch_gbif_data.py` 是“采集工具”，`build_knowledge_json.py` 是“正式构建工具”。

### `scripts/crawl_from_wikipedia.py`

作用：

- 调用 MediaWiki API 抓取英文 Wikipedia 鸟类页面
- 自动获取中文标题、摘要、页面原文提取和部分坐标
- 保存原始页面数据到 `data/wikipedia_raw/`
- 根据规则抽取 `distributed_in`、`lives_in`、`has_status`、`threatened_by`、`belongs_to`
- 自动写回 `data/birds.csv`、`data/locations.csv`、`data/relations.csv`

输入方式：

- `--titles "Red-crowned Crane" "Crested Ibis"`
- `--input-file path/to/titles.txt`
- `--input-file path/to/titles.csv`

说明：

- 抽取逻辑是规则型的，适合原型阶段批量整理
- `relations.csv` 中保留 `evidence`，方便后续人工审核
- 第一次抓取后，建议人工复核 `locations.csv` 和 `relations.csv`
- 如果启用 `--build-json`，脚本结束后会自动刷新前端使用的 `public/knowledge.json`

### `scripts/download_bird_name_list.py`

作用：

- 访问 AviList 官方 checklist 页面
- 自动发现当前 `short` 或 `extended` xlsx 下载链接
- 从官方 xlsx 中筛选 `Taxon_rank = species` 的标准鸟类名单
- 输出可直接被 `crawl_from_wikipedia.py --input-file` 读取的 `bird_titles.csv`

默认输出列：

- `page_title`
- `english_name`
- `scientific_name`
- `order`
- `family`
- `family_english_name`
- `iucn_red_list_category`
- `avibase_id`
- `range`
- `extinct_or_possibly_extinct`
- `source_dataset`
- `source_version`
- `source_url`

常用命令：

```bash
python scripts/download_bird_name_list.py
python scripts/download_bird_name_list.py --variant extended
python scripts/download_bird_name_list.py --output data/bird_titles.csv
```

说明：

- 默认只保留 `species` 行
- 默认排除已灭绝或可能灭绝物种
- 输出的 `page_title` 默认等于 AviList 英文名，便于后续直接批量喂给 Wikipedia 爬虫

## 12. 部署与预览

本地预览：

```bash
npm run build:data
npm run server
npm run dev
```

打包前端：

```bash
npm run build
```

打包后产物在 `dist/`。

如果只部署前端静态页面：

- 上传 `dist/` 到静态服务器即可

如果同时保留后端测试接口：

1. 部署 `dist/`
2. 部署 `server/`
3. 通过反向代理把 `/api` 转给 Node 服务

## 13. 推荐的数据维护习惯

后期你填数据时，建议按这个原则来：

- 鸟类本身的信息写到 `birds.csv`
- 地点本身的信息写到 `locations.csv`
- 事实关系写到 `relations.csv`
- 所有文本证据都尽量保留在 `evidence`
- 同一个实体只使用一个标准名称和一个稳定 `id`

最容易出错的地方是：

- 同一个地点写多个名字
- 同一个 `id` 对应多个名称
- 关系里引用了不存在的地点或鸟类

现在脚本已经会帮你拦住这类错误。

## 14. 下一步建议

这个版本已经完成“填表模式”的第一版闭环。你下一步最值得做的是：

1. 把更多物种逐步补进 `birds.csv`
2. 把文献或网页证据整理进 `relations.csv`
3. 需要时再把 `sample-docs.json -> relations.csv` 的人工审核流程做成半自动工具
