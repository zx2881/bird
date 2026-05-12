# Repository Guidelines

## 项目结构与模块组织
本仓库是“数据构建 + 前端可视化”项目。`data/` 保存主数据源，包括 `birds.csv`、`locations.csv`、`relations.csv`，以及抓取过程文件 `wikipedia_raw/`、`wikipedia_checkpoint/`。`scripts/` 存放 Python 数据脚本，核心入口是 `build_knowledge_json.py`。`public/knowledge.json` 是构建产物，供前端直接读取，不应长期手改。`src/` 是 Vue 3 前端，当前主要集中在 `App.vue`、`main.js`、`style.css`。

## 构建、运行与开发命令
```bash
npm run dev
npm run build
npm run preview
npm run build:data
npm run download:bird-names
npm run crawl:wikipedia -- --titles "Red-crowned Crane" --build-json
```
`npm run dev` 启动本地前端，`npm run build` 生成生产包，`npm run preview` 预览打包结果。`npm run build:data` 会读取 `data/*.csv` 并重建 `public/knowledge.json`，这是数据改动后的必跑命令。批量补数和抓取使用 `download:bird-names`、`crawl:wikipedia`。

## 编码风格与命名约定
前端文件延续现有风格：Vue、JS、CSS 统一使用 2 空格缩进，变量与函数采用 `camelCase`，组件文件使用 `PascalCase`。Python 脚本保留类型注解，函数命名使用 `snake_case`。数据层必须保持稳定 ID，例如 `bird-red-crowned-crane`、`loc-poyang-lake`；新增关系时优先复用已有实体 ID，并确保 CSV 使用 UTF-8 编码。

## 测试与验证
当前仓库未配置自动化测试框架，也没有覆盖率门槛。提交前至少完成两步验证：1. 运行 `npm run build:data`，确认 CSV、关系类型与实体映射无报错；2. 运行 `npm run build` 或 `npm run dev`，手动检查图谱、详情侧栏和地图联动是否正常。若后续补充测试，前端建议放在 `tests/` 或源码旁并使用 `*.test.js` 命名。

## 提交与 Pull Request 规范
现有 Git 历史以简短中文提交为主。后续建议继续使用简洁、明确的中文摘要，直接说明变更内容，例如“补充白鹤分布数据”或“修正图谱标签策略”。PR 应写清变更范围、涉及的 `data/` 或 `scripts/` 文件、验证命令；若修改前端展示，请附截图；若修改 CSV 结构或关系 Schema，请说明对 `public/knowledge.json` 的影响。

## 数据维护注意事项
不要把 `public/knowledge.json` 当作主数据源。任何实体、坐标、关系或摘要修正，应优先改 `data/*.csv` 或对应抓取脚本，再重新执行 `npm run build:data`。
