# 全球鸟类分布与生物多样性保护知识图谱构建

本项目已经从“单体 `knowledge.json` 一次性全量加载”重构为“CSV 主数据源 + 静态分片数据 + 前端按需异步扩展”的架构。

现在的数据层分为两层：

- `data/*.csv` 是长期维护的主数据源
- `public/data/*` 是构建脚本自动生成的静态 API 形态产物

这样做的目的很直接：

- 你继续维护结构化表格
- 前端不再一次性把全量鸟类、地点、关系全部塞进浏览器
- 后续扩展到 Avibase / AviList 级别的大数据量时，仍然可以在纯静态托管环境中运行

## 1. 当前项目包含什么

- `Vue 3 + Vite + Element Plus` 前端单页应用
- `3d-force-graph + three-spritetext` 的 WebGL 3D 图谱渲染层
- `Leaflet` 地图详情联动
- `data/` 目录下的 CSV 填表模式主数据源
- `scripts/build_knowledge_json.py` 的静态分片构建脚本
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
│  └─ data/
│     ├─ summary.json
│     ├─ graph_preview.json
│     ├─ taxonomy_skeleton.json
│     └─ nodes/
│        ├─ bird-red-crowned-crane.json
│        └─ taxonomy-family-gruidae.json
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
│  ├─ graph/
│  │  └─ SigmaCanvas.vue
│  ├─ stores/
│  │  └─ graphStore.js
│  └─ views/
│     ├─ Home.vue
│     └─ BirdDetail.vue
├─ index.html
├─ package.json
└─ vite.config.js
```

## 3. 静态分片模式怎么工作

现在的数据流是：

1. 你维护 `data/birds.csv`
2. 你维护 `data/locations.csv`
3. 你维护 `data/relations.csv`
4. 运行 `python scripts/build_knowledge_json.py`
5. 自动生成 `public/data/summary.json`
6. 自动生成 `public/data/taxonomy_skeleton.json`
7. 自动生成 `public/data/graph_preview.json`
8. 自动生成 `public/data/nodes/[node_id].json`

也就是：

- 表格是“主数据”
- `public/data/*` 是“构建产物”
- 首页先加载轻量预览图
- 前端只在需要的时候请求某个节点的局部详情切片

### 三类输出各自做什么

#### `public/data/summary.json`

作用：

- 只保留鸟类轻量索引
- 用于首页搜索框做极速匹配
- 不携带整图关系，不进入重渲染路径

结构上只保留：

- `id`
- `name`
- `englishName`
- `latinName`

#### `public/data/taxonomy_skeleton.json`

作用：

- 只保留高层级分类学骨架
- 当前默认承载“目 -> 科”节点与关系
- 用作分类视图、调试和后续扩展的保留骨架数据

它仍然由构建脚本输出，但首页主图现在不再先加载这份骨架，而是直接走 `graph_preview.json`。

#### `public/data/graph_preview.json`

作用：

- 承载首页“轻量预览图”
- 包含所有物种节点、目 / 科节点、预计算 `x / y / z` 坐标
- 只保留首页真正需要的最小字段和轻量关系，避免把详情属性和上下文边一次性塞进浏览器

当前默认总览图只保留这两类关系：

- `bird -> family`
- `family -> order`

前端首页不会直接照搬这份文件里的分类聚团坐标，而是把这些轻量节点重新映射到一个稳定的 3D 球形体积分布中，让全图先以“空间内均匀分散”的方式展开，再在点击时按需请求详情切片。

#### `public/data/nodes/[node_id].json`

作用：

- 为每个物种或分类节点提供单独切片
- 前端在点击或搜索命中时再请求
- 文件内部包含该中心节点的详细属性、1 度邻居节点与关系边

当前实现里，以下节点会生成独立切片：

- 每个 `bird`
- 每个 `taxonomy family`
- 每个 `taxonomy order`

## 4. 为什么要从单体 JSON 改成静态分片

旧架构的问题很明确：

- 构建阶段把所有 CSV 打进一个 `public/knowledge.json`
- 浏览器首屏一次性下载并反序列化整份数据
- 物种数量、地点数量、关系数量一上去，内存和渲染压力会同时爆炸

新架构的收益是：

- 首屏加载搜索索引和 `graph_preview.json`
- 详情与关系网络改成按需拉取
- GitHub Pages 这类纯静态托管也能部署
- PWA 不再预缓存全量大 JSON，而改为对 `/data/*.json` 做运行时缓存

## 5. 三个 CSV 文件怎么填

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
- `genus`: （可选）属（英文科学名）
- `species`: （可选）种（英文科学名，优先写入 Wikidata 的 `P225` 学名）
- `order_cn`: （可选）目（中文名）
- `family_cn`: （可选）科（中文名）
- `genus_cn`: （可选）属（中文名）
- `species_cn`: （可选）种（中文名，通常对应鸟类中文常用名）

示例：

```csv
id,name,english_name,latin_name,summary,lat,lng,image_url,order,family,genus,species,order_cn,family_cn,genus_cn,species_cn
bird-siberian-crane,白鹤,Siberian Crane,Leucogeranus leucogeranus,大型涉禽，依赖湿地和浅水湖泊。,29.103,116.221,,,,,,,,
```

说明：

- `birds.csv` 只保存鸟类本身信息
- `status`、`habitats`、`threats`、`locations` 不直接写在这里
- 这些字段会由 `relations.csv` 自动聚合出来
- `order/family` 会进一步在构建阶段生成分类骨架节点和关系

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

另外补了 3 个工程字段：

- `subject_id`
- `object_id`
- `object_summary`

原因很明确：

- 前端构图必须依赖稳定 `id`
- 只靠中文名称连接节点，后期很容易重名或改名
- `object_summary` 让你在不新增第四张表的前提下，也能给 Habitat / Status / Threat / Taxon 节点补说明

## 6. 目前支持的关系类型

`relations.csv` 里当前支持：

- `distributed_in`
- `lives_in`
- `has_status`
- `threatened_by`
- `belongs_to`

说明：

- 前四种是主要的业务关系
- `belongs_to` 仍可用于手工维护分类关系
- 构建脚本还会根据 `birds.csv` 中的 `order/family` 自动补出两类前端内部关系：
  - `belongs_to_family`
  - `belongs_to_order`

这两类内部关系主要用于生成首屏分类骨架和分类切片，一般不需要你手工维护。

如果你后续要继续使用 `belongs_to`：

- 建议在 `relations.csv` 中把 `object_type` 写成 `Taxon`
- 构建脚本会把它映射成前端里的 `taxonomy` 节点

## 7. 构建脚本说明

### `scripts/build_knowledge_json.py`

作用：

- 读取 `data/birds.csv`
- 读取 `data/locations.csv`
- 读取 `data/relations.csv`
- 验证关系、实体和名称是否一致
- 自动生成 `public/data/*` 静态分片
- 自动删除旧的 `public/knowledge.json`

脚本现在主要做了 7 件事：

1. 读取三张 CSV
2. 先创建 Bird 和 Location 节点
3. 再从 `relations.csv` 自动创建 Habitat / Status / Threat / Taxon 节点
4. 自动为每只鸟聚合出：
   - `locations`
   - `habitats`
   - `threats`
   - `status`
5. 根据 `birds.csv` 的 `order/family` 补出分类学骨架节点和关系
6. 预计算节点坐标（`x / y / z`），避免前端在大图上实时力导向抖动
7. 输出 `summary.json + taxonomy_skeleton.json + graph_preview.json + nodes/*.json`

### 为什么这个脚本很重要

因为它会帮你提前发现填表错误，例如：

- 同一个 `object_id` 对应两个不同名称
- `relations.csv` 里写了一个不存在的地点
- `subject` 名称和 `birds.csv` 对不上
- `predicate` 写错

这种错误如果等到前端报错再查，会很慢；现在在构建阶段就能直接发现。

## 8. 前端现在怎么配合这个模式

### `src/App.vue`

作用：

- 应用启动时先触发 `graphStore.loadInitialData()`
- 首页随后异步触发 `graphStore.loadGraphPreview()`
- 首屏不再请求全量图数据，也不再批量请求所有节点切片

### `src/stores/graphStore.js`

作用：

- 首屏加载 `summary.json`
- 首页再异步加载 `graph_preview.json`
- 在搜索命中、点击鸟类或点击分类节点时，再异步拉取 `nodes/[node_id].json`
- 用增量合并方式把新节点和新关系织入当前图数据

### `src/graph/SigmaCanvas.vue`

作用：

- 使用 `3d-force-graph` 渲染图谱
- 不走 SVG，而是走 WebGL 3D 场景
- 图实例常驻，后续只对节点和边做增量更新

当前做了两类性能优化：

- 标签策略：默认不常驻文字标签，名称与分类通过 Hover 提示层查看
- 布局稳定：优先使用 Python 预计算 `x / y / z` 坐标，而不是在浏览器里对海量节点持续跑力导向

### 为什么首页现在是“空间内均匀分散”，而不是长方体盒子

首页主图的“均匀分布”已经从旧的二维网格抖动，改成了真正的三维体积分布。

当前前端会对 `graph_preview.json` 中的轻量节点做一次稳定的球形重排：

1. 方向均匀：

- 每个节点通过稳定哈希生成自己的 `theta / phi`
- 这样节点会在三维空间中朝不同方向发散，而不是只铺在一个平面或矩形网格上

2. 半径按体积均匀：

- 半径不是线性增长，而是按 `cbrt(t)` 取值
- 这样得到的是“球体内部均匀采样”，不是只堆在球壳表面，也不是塞进长方体盒子

3. 质心回零：

- 前端会在生成全部预览点后重新计算整体质心
- 再把整团点平移回场景中心，避免球团整体偏到画布一侧

所以当前首页看到的主图，目标不是“按分类聚成几团”，而是：

- 所有轻量节点先在空间里均匀散开
- 用户点击某个节点后，再把该节点的一度邻域贴靠到它附近展开
- 全图保持安静，局部交互时才短暂唤醒

### 现在的图谱为什么不再“一边卡一边动”

目前图谱不是传统意义上的“全量实时物理模拟”，而是“预计算坐标 + 局部瞬时唤醒”的混合模式。

原理分成三段：

1. 常态：零算力静止

- `build_knowledge_json.py` 会在构建阶段为节点写入稳定的 `x / y / z`
- 前端加载后，默认把每个节点都钉死在自己的 home 坐标上
- 这样用户平时只是在转相机、缩放和查看，浏览器不会持续对上千上万个节点跑布局求解

2. 拖拽瞬间：只唤醒局部邻域

- 当用户拖拽某个节点时，前端不会释放整张图
- 只会临时释放被拖拽节点及其一跳邻居
- 这时会短暂 reheat 一次局部模拟，让拖拽产生“果冻式”的局部拉伸感

3. 松手之后：自动回锚

- 松手后，这一小撮被释放的节点会向自己的 home 坐标回弹
- 回弹结束后再次固定
- 页面重新回到“静止、低算力、可继续浏览”的状态

这套模式的目标不是让万级节点一直运动，而是：

- 打开时不炸显卡
- 浏览时不持续抖动
- 真正交互时仍然保留一点动态弹性反馈

### 为什么首页现在不再批量请求所有物种切片

之前首页为了“把所有物种放进图里”，会后台把每个物种的 `nodes/[node_id].json` 都请求一遍。

这会带来两类额外开销：

- 上千个静态文件请求
- 每一批返回后都要做一次并图和重渲染

现在首页改成一次性读取 `graph_preview.json`：

- 只发 1 次轻量预览请求
- 先把所有物种节点和分类边放进图里
- 单个物种的详情、地点、栖息地、威胁、保护等级，仍然在点击后按需读取 `nodes/[node_id].json`

这样“看全图”和“看详情”被拆成了两条不同的性能路径。

### `src/views/Home.vue`

当前首页交互是：

- 首屏先加载搜索索引
- 然后一次性加载 `graph_preview.json`，把全部物种的轻量节点织入当前图谱
- 这些轻量节点只带类别、名字、最小分类信息和轻量关系
- 首页图谱会把这些轻量节点重新映射为稳定的 3D 球形均匀散点云
- 搜索命中鸟类时，先按需加载该物种切片，再跳转详情页
- 点击图中鸟类节点时，先按需加载该物种切片，再跳转详情页
- 点击图中分类节点时，留在当前页面继续扩展图谱

### `src/views/BirdDetail.vue`

详情页现在不再依赖全量预载。

当前逻辑是：

- 先确保 `summary.json` 已加载
- 再按路由中的物种 `id` 异步拉取对应 chunk
- 然后渲染详情文本、地点、关系和地图

## 9. 不再使用 `public/knowledge.json`

`public/knowledge.json` 已经从主流程中移除。

现在你应该：

- 改 `data/*.csv`
- 运行构建脚本
- 让脚本输出 `public/data/*`

不建议再恢复单体 JSON 作为前端运行入口。

## 10. 命令怎么用

安装前端依赖：

```bash
npm install
```

从 CSV 生成静态分片数据：

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

## 11. 当前分片输出的大致规模

当前本地一次构建结果大致为：

- `summary.json` 约 `193.88 KB`
- `taxonomy_skeleton.json` 约 `0.47 KB`
- `nodes/*.json` 共 `2106` 个
- 单个节点切片平均约 `4.77 KB`
- 当前最大节点切片约 `60.02 KB`

这组数字的意义是：

- 首屏索引和骨架都足够轻
- 大部分节点切片都很小
- 前端每次只增量请求局部邻域，而不是全量下载整图

随着你继续扩展数据集，这些数字会变化，但架构本身不会变。

## 12. GitHub Pages / PWA 部署说明

项目当前支持纯静态部署，包括 GitHub Pages。

当前部署策略是：

- Vite `base` 已配置为 GitHub Pages 子路径
- `public/data/*.json` 作为静态资源直接随站点发布
- PWA 不再把全量图数据做 precache
- `/data/*.json` 改为 Workbox 运行时缓存

这样做的原因是：

- precache 适合小而稳定的静态资源
- 大量节点切片更适合访问时缓存
- 可以避免 Service Worker 在构建时因为超大 JSON 失败

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

## 13. 数据维护习惯

后期你填数据时，建议按这个原则来：

- 鸟类本身的信息写到 `birds.csv`
- 地点本身的信息写到 `locations.csv`
- 事实关系写到 `relations.csv`
- 所有文本证据都尽量保留在 `evidence`
- 同一个实体只使用一个标准名称和一个稳定 `id`
- 改完数据后统一执行 `npm run build:data`

最容易出错的地方是：

- 同一个地点写多个名字
- 同一个 `id` 对应多个名称
- 关系里引用了不存在的地点或鸟类
- 分类字段 `order/family` 更新了，但没有重新构建分片

现在脚本已经会帮你拦住大部分这类错误。

## 14. 采集脚本说明

### `scripts/fetch_gbif_data.py`

作用：

- 从 GBIF 抓带坐标的 occurrence 记录
- 演示如何把外部分布点转成前端兼容数据

它和填表模式的关系是：

- 你可以先用它抓到分布点
- 再把整理后的结果写回 `locations.csv` 和 `relations.csv`
- 最后统一由 `build_knowledge_json.py` 输出静态分片

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
- 如果启用 `--build-json`，脚本结束后会自动刷新 `public/data/*`

### 鸟类图片获取

`crawl_from_wikipedia.py` 在抓取时通过 MediaWiki API 的 `prop=pageimages` 参数自动获取 Wikipedia 页面题图（800px 缩略图），存入 `birds.csv` 的 `image_url` 列。前端会在 `image_url` 有值时展示真实鸟类图片，无值时降级为占位展示。

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

- 通过 Wikipedia + Wikidata API 获取每个鸟类的分类信息
- 自动抽取“目 / 科 / 属 / 种”四层级的英文科学名与中文名
- 回填到 `birds.csv` 的 `order`、`family`、`genus`、`species`、`order_cn`、`family_cn`、`genus_cn`、`species_cn` 列
- 为前端分类骨架准备稳定字段，其中图谱骨架仍默认只使用“目 / 科”两层，避免节点膨胀

数据流：

1. 读取 `birds.csv` 中的 `english_name` 和 `latin_name`
2. 优先走 en.wikipedia 标题解析，失败后再走 Wikipedia 搜索 / Wikidata 搜索拿到 QID
3. 沿 Wikidata 的 P171（上级分类）链条向上遍历
4. 非中文字段优先读取 `P225` 学名，中文字段读取 `zh` 标签
5. 写入 `birds.csv`
6. 重新执行 `build:data`，让分类骨架和物种切片刷新

常用命令：

```bash
# 获取所有鸟类的分类标签
python scripts/fetch_taxonomy.py

# 强制重取并刷新前端数据
python scripts/fetch_taxonomy.py --overwrite --build-json

# 通过代理访问
python scripts/fetch_taxonomy.py --proxy http://127.0.0.1:7890 --delay 0.1
```

说明：

- 脚本支持断点续跑：已经具备 `order / family / genus / species` 的鸟类会自动跳过
- 不再写入“纲”，当前项目只保留 `目 / 科 / 属 / 种`
- 同一分类实体会命中本地缓存，批量抓取时不会对同一属 / 科 / 目重复请求
- 每成功抓到 1 条鸟类分类信息就会立即写盘；即使中途 `Ctrl+C`，之前成功的记录也不会丢
- 分类骨架节点并不要求你手工维护到 `relations.csv`
- 接口调用遵守 Wikidata 限速要求，默认 0.1s 最小请求间隔，并配合本地缓存减少重复请求

### GBIF / 中国观鸟记录中心坐标获取

项目根目录下的 `gbif_coord_fetcher.py` 和 `china_bird_coord_fetcher.py` 现已默认读写 `data/birds.csv`，确保坐标补全不会在 `build:data` 时丢失。

常用命令：

```bash
# GBIF 全球搜索，只填补空坐标（默认写入 data/birds.csv）
python gbif_coord_fetcher.py --null-only

# 中国观鸟记录中心（需要 Token）
python china_bird_coord_fetcher.py --token YOUR_TOKEN --null-only
```

推荐工作流：坐标补全后执行 `npm run build:data` 刷新静态分片。

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

## 15. 下一步建议

这个版本已经完成了“静态分片 + 异步增量图谱”的主干闭环。后续最值得继续推进的是：

1. 把更多物种持续补进 `birds.csv`
2. 把文献或网页证据整理进 `relations.csv`
3. 继续完善 `Overview`、`Categories`、`Editor` 等页面对 summary/chunk 语义的适配
4. 如果未来要做全球 11,000+ 物种级别图谱，可继续增加：
   - 按科或按地理区域的二级索引
   - 更细粒度的分层缓存
   - 后台预计算社区结构或聚类信息
