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
- `scripts/fetch_taxonomy.py` 的 Wikidata 分类标签获取脚本
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
│  ├─ fetch_bird_images.py
│  ├─ fetch_taxonomy.py
│  └─ fetch_gbif_data.py
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
- `image_url`: （可选）鸟类图片 URL，由 Wikipedia 抓取脚本自动填充
- `order`: （可选）目（英文科学名），由 `fetch_taxonomy.py` 自动填充
- `family`: （可选）科（英文科学名），由 `fetch_taxonomy.py` 自动填充
- `order_cn`: （可选）目（中文名）
- `family_cn`: （可选）科（中文名）

示例：

```csv
id,name,english_name,latin_name,summary,lat,lng,image_url
bird-siberian-crane,白鹤,Siberian Crane,Leucogeranus leucogeranus,大型涉禽，依赖湿地和浅水湖泊。,29.103,116.221,
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

如需通过代理访问 Wikipedia：

```bash
npm run crawl:wikipedia -- --titles "Red-crowned Crane" --proxy http://127.0.0.1:7890 --build-json
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
- `data/wikipedia_checkpoint/*.json`

`crawl_from_wikipedia.py` 现在支持断点续跑：

- 每处理完一个标题就会立刻落盘到 CSV 和 checkpoint
- 再次运行时会自动跳过已经完成的标题
- 如果上次运行中断，会先从 `data/wikipedia_checkpoint/` 补齐 CSV，再继续后面的标题
- 如果你确实要强制重抓，传 `--overwrite`

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
- 通过 `prop=pageimages` 自动获取 Wikipedia 页面题图 URL（800px 缩略图），写入 `birds.csv` 的 `image_url` 列
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

### 鸟类图片获取

`crawl_from_wikipedia.py` 在抓取时通过 MediaWiki API 的 `prop=pageimages` 参数自动获取 Wikipedia 页面题图（800px 缩略图），存入 `birds.csv` 的 `image_url` 列。前端会在 `image_url` 有值时展示真实鸟类图片，无值时降级为随机占位图。

**为已有鸟类补图：**

如果 `birds.csv` 中已有数据但缺少 `image_url`，使用 `--overwrite` 参数重新抓取即可自动补图：

```bash
python scripts/crawl_from_wikipedia.py --titles "Red-crowned Crane" --overwrite --build-json
```

或者批量补图：

```bash
python scripts/crawl_from_wikipedia.py --input-file data/bird_titles.csv --overwrite --build-json
```

`--overwrite` 会用新抓取的非空字段覆盖已有数据，原有 `summary`、`lat`、`lng` 等字段不受影响。

**仅批量补图（推荐）：**

如果只缺图片不想重新抓取完整页面，可用专用的图片获取脚本，每批 50 个标题批量查询，速度极快：

```bash
npm run fetch:bird-images
# 或带代理
python scripts/fetch_bird_images.py --proxy http://127.0.0.1:7890
```

脚本读取 `birds.csv` 中所有 `image_url` 为空的鸟类，通过 Wikipedia `prop=pageimages` API 批量获取题图 URL 并写回 CSV，最后需执行 `npm run build:data` 刷新前端数据。


### `scripts/fetch_taxonomy.py`

作用：

- 通过 Wikidata API 获取每个鸟类的完整分类信息（界门纲目科属种）
- 自动抽取"目"和"科"两层级的英文/中文名称
- 回填到 `birds.csv` 的 `order`、`family`、`order_cn`、`family_cn` 列
- 同时生成 `belongs_to` 关系到 `relations.csv`

数据流：

1. 读取 `birds.csv` 中的 `english_name`
2. 通过 en.wikipedia API 获取 Wikidata QID
3. 沿 Wikidata 的 P171（上级分类）链条向上遍历
4. 收集各层级的英文/中文标签
5. 写入 `birds.csv` 和 `relations.csv`

常用命令：

```bash
# 获取所有鸟类的分类标签
python scripts/fetch_taxonomy.py

# 强制重取并刷新前端数据
python scripts/fetch_taxonomy.py --overwrite --build-json

# 通过代理访问
python scripts/fetch_taxonomy.py --proxy http://127.0.0.1:7890 --delay 0.5
```

说明：

- 脚本支持断点续跑：已有分类信息的鸟类会自动跳过
- 界(Animalia 动物界)/门(Chordata 脊索动物门)/纲(Aves 鸟纲) 对所有鸟类恒定，不会重复写入
- 生成的关系中 `object_type` 为 `Taxon`，前端会映射为 `taxonomy` 节点
- 接口调用遵守 Wikidata 限速要求，默认 0.5s 延迟


### GBIF / 中国观鸟记录中心坐标获取

项目根目录下的 `gbif_coord_fetcher.py` 和 `china_bird_coord_fetcher.py` 现已默认读写 `data/birds.csv`（而非 `knowledge.json`），确保坐标补全不会在 `build:data` 时丢失。

常用命令：

```bash
# GBIF 全球搜索，只填补空坐标（默认写入 data/birds.csv）
python gbif_coord_fetcher.py --null-only

# 中国观鸟记录中心（需要 Token）
python china_bird_coord_fetcher.py --token YOUR_TOKEN --null-only
```

推荐工作流：坐标补全后执行 `npm run build:data` 刷新前端 JSON。


### 主爬虫改进（v0.2）

以下改进已合入 `scripts/crawl_from_wikipedia.py`：

- **单鸟失败不再终止整批**：主循环添加 `try/except`，某个标题出错后记录错误继续下一个
- **威胁关系去重优化**：`threatened_by` 去重键从 `(object_id, evidence)` 改为 `object_id`，避免同一威胁因不同证据语句产生重复条目
- **分类列预留**：`birds.csv` 新增 `order`、`family`、`order_cn`、`family_cn` 四列，由 `fetch_taxonomy.py` 填充


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
npm run dev
```

打包前端：

```bash
npm run build
```

打包后产物在 `dist/`。

如果只部署前端静态页面：

- 上传 `dist/` 到静态服务器即可

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
