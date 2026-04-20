# 全球鸟类分布与生物多样性保护知识图谱构建

本项目基于你提供的两份需求文档搭建了一个完整框架，包含：

- `Vue 3 + Vite + Element Plus` 前端单页应用
- `ECharts` 力导向知识图谱与 `Leaflet` 地图联动
- `public/knowledge.json` 静态知识图谱样例数据
- `Node` 简易后端三元组抽取测试接口
- `pygbif` 抓取脚本示例，用于生成兼容的 `knowledge.json`

## 1. 目录结构

```text
.
├─ public/
│  └─ knowledge.json
├─ scripts/
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
├─ vite.config.js
└─ README.md
```

## 2. 项目初始化指令

如果你想从空目录重新创建同类项目，可以使用下面的命令：

```bash
npm create vite@latest global-bird-knowledge-graph -- --template vue
cd global-bird-knowledge-graph
npm install
npm install element-plus echarts leaflet
```

当前目录里的 `package.json` 已经按这个思路配置好了，因此你在本项目中只需要执行：

```bash
npm install
```

## 3. 如何运行

前端与后端建议分别开两个终端。

终端 1，启动三元组测试后端：

```bash
npm run server
```

终端 2，启动 Vue 前端：

```bash
npm run dev
```

默认地址：

- 前端：`http://localhost:5173`
- 后端：`http://localhost:3001`

`vite.config.js` 已经把 `/api` 代理到了 `3001` 端口，所以前端里可以直接请求 `/api/triples/test`。

## 4. 前端代码说明

### `package.json`

作用：

- 定义 Vue/Vite 的依赖
- 安装 `Element Plus`、`ECharts`、`Leaflet`
- 提供 `dev`、`build`、`preview`、`server` 四个脚本

### `vite.config.js`

作用：

- 注册 Vue 插件
- 将开发服务器端口固定为 `5173`
- 把 `/api` 请求代理到本地后端 `http://localhost:3001`

### `src/main.js`

作用：

- 创建 Vue 应用实例
- 全局注册 `Element Plus`
- 引入 `Element Plus`、`Leaflet` 和自定义样式

### `src/App.vue`

这是前端核心页面，基本把你的布局要求全部落在了一个文件里，便于你继续扩展。

主要分成四部分：

1. 页面布局
   - 顶部 `Header` 展示标题“全球鸟类多样性知识探索平台”
   - 左侧 `30%` 为概览、搜索、实体详情、后端测试面板
   - 右侧 `70%` 上方为 ECharts 力导向图，下方为 Leaflet 地图

2. 静态知识图谱加载
   - `loadKnowledge()` 从 `public/knowledge.json` 读取 `nodes` 和 `links`
   - 初始默认选中第一种鸟类并同步地图定位

3. 图谱与地图联动
   - `initChart()` 初始化力导向图
   - 点击图谱中的节点时，通过 `selectEntity()` 更新左侧详情
   - 如果点中地点或带坐标的鸟类，`moveMap()` 会自动飞到对应位置并打点

4. 后端三元组测试
   - 点击“运行三元组抽取测试”后，请求 `/api/triples/test`
   - 前端将返回的 `documents` 与 `triples` 直接展示在左侧表格中

### `src/style.css`

作用：

- 统一定义颜色、阴影、玻璃态面板等全局变量
- 实现左右双栏布局和上下分屏布局
- 对图谱卡片、地图卡片、指标卡片、实体详情卡片进行视觉统一
- 补充移动端响应式布局

视觉上没有走默认的白底后台风格，而是做了偏自然调查面板的暖色渐变和半透明卡片，便于后续继续迭代。

## 5. 静态图谱数据说明

### `public/knowledge.json`

作用：

- 作为前端主数据源
- 满足 `static-data` 模式
- 提供 `nodes` 和 `links` 两个数组

数据内容：

- 10 个鸟类节点
  - 丹顶鹤
  - 朱鹮
  - 中华秋沙鸭
  - 勺嘴鹬
  - 黑脸琵鹭
  - 加州神鹫
  - 菲律宾鹰
  - 鸮鹦鹉
  - 帝企鹅
  - 灰冠鹤
- 10 个地点节点
- 8 个栖息地节点
- 4 个保护等级节点
- 8 个威胁因素节点

字段设计：

- `id`: 节点唯一标识
- `name`: 节点名称
- `type`: 节点类型，前端依靠它决定颜色和行为
- `lat` / `lng`: 所有节点都保留该属性；无空间意义的节点使用 `null`
- 鸟类节点额外包含：
  - `englishName`
  - `latinName`
  - `status`
  - `summary`
  - `locations`
  - `habitats`
  - `threats`

关系设计：

- `distributed_in`
- `lives_in`
- `has_status`
- `threatened_by`

这里没有加入 `belongs_to`，原因是你给出的三元组 Schema 中并未为“科/目”定义独立实体类型。为了保持前后端 Schema 一致，当前演示版本先聚焦前四种关系。

## 6. 后端代码说明

### `server/index.js`

作用：

- 启动一个零依赖 Node HTTP 服务
- 提供健康检查接口 `GET /api/health`
- 提供演示抽取接口 `GET /api/triples/test`
- 提供自定义文本抽取接口 `POST /api/triples/extract`

这样做的好处是：

- 不依赖 `express`
- 安装成本低
- 便于你以后替换成真正的知识抽取服务

### `server/data/sample-docs.json`

作用：

- 存放少量“从网络资料整理后的测试文本”
- 每条文档都带有 `source_url`
- 供后端批量运行抽取逻辑

当前内置了 4 条测试文本：

- 丹顶鹤
- 朱鹮
- 勺嘴鹬
- 黑脸琵鹭

这些文本是根据公开网页资料整理的简化测试句，并不是完整转载原文。这样做是为了：

- 保留网络来源
- 满足你的“从网络寻找少量数据”要求
- 同时避免把后端测试写成不可控的实时爬虫

### `server/services/tripleExtractor.js`

作用：

- 根据 `三元组提取.md` 的 Schema 进行规则抽取
- 输出严格的 JSON 三元组数组

主要逻辑：

1. `splitSentences(text)`
   - 先按中文句号、问号、感叹号切句

2. `extractTriplesFromText(text)`
   - 在每个句子中先识别主语鸟类
   - 再根据关键词判断关系类型
   - 从词表中抽取地点、栖息地、保护等级、威胁因素

3. `uniqueTriples(triples)`
   - 去除重复三元组

当前提取策略是“演示型规则抽取”，优点是简单、可控、容易替换。后续如果你要做真正的抽取系统，可以把这里替换为：

- LLM 抽取
- spaCy / HanLP / LTP
- 正则 + 词典 + 依存句法混合方案

## 7. pygbif 脚本说明

### `scripts/fetch_gbif_data.py`

作用：

- 演示如何调用 `pygbif.species.name_backbone()` 获取分类键
- 演示如何调用 `pygbif.occurrences.search()` 拉取带坐标的 occurrence
- 将 GBIF occurrence 坐标转换成前端需要的 `nodes + links` 结构

脚本流程：

1. 在 `BIRD_SEEDS` 中维护 10 个目标物种
2. 用 `name_backbone()` 获取每个物种的 `usageKey`
3. 用 `occurrences.search()` 拉取坐标记录
4. 抽取前几个 occurrence 转为地点节点
5. 为每个鸟类节点补上本地配置的状态、栖息地和威胁关系
6. 输出为 `knowledge.generated.json`

运行方式：

```bash
pip install pygbif
python scripts/fetch_gbif_data.py --limit 15 --output public/knowledge.generated.json
```

注意：

- GBIF 偏向分布记录，并不直接提供完整 IUCN 保护等级体系
- 所以脚本里把状态、威胁和栖息地作为“本地补充字段”
- 这正适合你当前“网页演示 + 知识图谱原型”阶段

## 8. 本地预览与打包部署

### 本地预览

```bash
npm install
npm run server
npm run dev
```

打开浏览器访问 `http://localhost:5173`。

### 打包前端

```bash
npm run build
```

执行后会生成 `dist/` 文件夹，这就是可部署到静态服务器的前端产物。

### 本地查看打包结果

```bash
npm run preview
```

### 部署方式建议

如果你只想部署静态图谱页面：

- 直接将 `dist/` 上传到 Nginx、Apache 或任意静态托管平台

如果你要保留三元组测试后端：

1. 前端部署 `dist/`
2. 后端部署 `server/` 到一台 Node 服务器
3. 让反向代理把 `/api` 转发到 Node 服务

Nginx 思路如下：

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        root /var/www/bird-kg;
        try_files $uri $uri/ /index.html;
    }

    location /api/ {
        proxy_pass http://127.0.0.1:3001/api/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## 9. 网络资料来源

后端测试文本目前主要依据以下公开页面整理，检查日期为 `2026-04-20`：

- Red-crowned Crane: <https://en.wikipedia.org/wiki/Red-crowned_crane>
- Crested Ibis: <https://en.wikipedia.org/wiki/Crested_ibis>
- Spoon-billed Sandpiper: <https://en.wikipedia.org/wiki/Spoon-billed_sandpiper>
- Black-faced Spoonbill: <https://en.wikipedia.org/wiki/Black-faced_spoonbill>
- pygbif species API: <https://pygbif.readthedocs.io/en/latest/modules/species.html>
- pygbif occurrences API: <https://pygbif.readthedocs.io/en/latest/modules/occurrences.html>

## 10. 下一步建议

这个版本已经可以作为“第一阶段框架”。你下一步可以继续做三件事：

1. 把 `tripleExtractor.js` 替换成真实的 LLM 抽取接口
2. 把 `knowledge.json` 改造成从 Neo4j、ArangoDB 或 NebulaGraph 动态读取
3. 在地图层加入迁飞路线、保护区边界和时间筛选
#   b i r d  
 