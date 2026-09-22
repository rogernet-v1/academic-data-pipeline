```markdown
# 🎓 Academic Data Pipeline (学术数据高并发采集与 ETL 管道)

[![Python Version](https://img.shields.io/badge/Python-3.10%2B-blue?style=flat-square&logo=python)](https://www.python.org/)
[![SQLAlchemy](https://img.shields.io/badge/ORM-SQLAlchemy%202.0-red?style=flat-square&logo=sqlalchemy)](https://www.sqlalchemy.org/)
[![Redis](https://img.shields.io/badge/Cache-Redis-DC382D?style=flat-square&logo=redis)](https://redis.io/)
[![Asyncio](https://img.shields.io/badge/Async-asyncio%20%2F%20httpx-00599C?style=flat-square)](https://docs.python.org/3/library/asyncio.html)
[![License](https://img.shields.io/badge/License-MIT-green.svg?style=flat-square)](LICENSE)

> 一个基于 Python 异步协程 (Asyncio)、Redis 去重与 SQLAlchemy 2.0 ORM 构建的高性能学术数据采集、解密签名与增量落库 ETL 管道系统。

---

## 🏛️ 系统架构 (Architecture)

系统采用典型的**解耦式数据管道架构**，保证数据抓取、逆向签名、去重过滤与持久化存储之间的高度模块化与独立可扩展性：


```

+-------------------+      +----------------------+      +----------------------+
|  arXiv / API      | <--->|  Spiders & Parsers   |<---> |  Request Signer      |
|  (Data Sources)   |      |  (httpx / asyncio)   |      |  (JS Reverse / MD5)  |
+-------------------+      +----------------------+      +----------------------+
|
v
+----------------------+
|  Redis Deduplicator  |  (Set/Bloom Incremental Filter)
+----------------------+
|
v
+----------------------+
| SQLAlchemy 2.0 ORM   |  (Async Engine & Upsert)
+----------------------+
|
v
+----------------------+
|  Relational DB       |  (SQLite / PostgreSQL)
+----------------------+

```

---

## ✨ 核心特性 (Key Features)

1. **⚡ 高性能异步协程架构**
   - 全流程基于 `asyncio` 与 `httpx` 构建，非阻塞 I/O 设计，单节点具备高并发吞吐能力。

2. **🔑 Web 逆向工程与请求签名**
   - 内部集成 `PyExecJS` 逆向签名模块 (`signer.py`)，支持动态执行 JavaScript 前端加密逻辑，模拟真实场景下的 Token/Sign 校验破解与安全反爬绕过。

3. **🛡️ Redis 毫秒级增量去重**
   - 基于 Redis 异步连接池实现的 Set 去重机制，支持海量数据抓取前的毫秒级去重拦截与增量状态回写，大幅节省网络与数据库开销。

4. **💾 数据库幂等落库 (SQLAlchemy 2.0 Async)**
   - 使用 SQLAlchemy 2.0 声明式异步 ORM，配合数据库原生的 `UPSERT` 语法（ON CONFLICT DO UPDATE），确保管道具备严格的数据幂等性与重复写入自愈能力。

5. **🛡️ 稳健的资源回收与日志管控**
   - 包含完整的优雅退出（Graceful Shutdown）机制与全局规范化日志输出，防止数据库连接池与 Redis 连接泄漏。

---

## 🛠️ 项目结构 (Project Directory)

```text
academic-data-pipeline/
├── core/
│   ├── __init__.py
│   └── pipeline.py       # SQLAlchemy 2.0 异步 ORM 数据模型与 Upsert 管道
├── spiders/
│   ├── __init__.py
│   └── arxiv_spider.py   # arXiv 学术数据异步提取与 Atom XML 结构化解析器
├── utils/
│   ├── __init__.py
│   ├── redis_client.py   # Redis 异步连接池与增量去重过滤器
│   └── signer.py         # PyExecJS 逆向签名与反爬 Token 生成器
├── main.py               # 管道主控调度引擎 (Orchestration Engine)
├── requirements.txt      # 依赖配置文件
└── README.md             # 项目架构与说明文档

```

---

## 🚀 快速开始 (Quick Start)

### 1. 克隆项目与安装依赖

```bash
git clone git@github.com:rogernet-v1/academic-data-pipeline.git
cd academic-data-pipeline

# 创建并激活虚拟环境 (可选)
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt

```

### 2. 环境配置

* 确保本地已启动 **Redis** 服务（默认端口 `6379`）。若未安装 Redis，系统将自动平滑降级运行。

### 3. 运行管道主引擎

```bash
python main.py

```

---

## 📈 运行日志示例 (Execution Log)

```text
2026-09-22 14:10:00 [INFO] academic_pipeline.main - === 启动学术数据异步采集与分析管道 ===
2026-09-22 14:10:00 [INFO] core.pipeline - 数据库初始化完成，数据表结构准备就绪。
2026-09-22 14:10:01 [INFO] utils.redis_client - Redis 去重客户端连接成功。
2026-09-22 14:10:01 [INFO] spiders.arxiv_spider - 正在发起学术 API 异步请求: query=cat:cs.AI, max_results=5
2026-09-22 14:10:02 [INFO] spiders.arxiv_spider - 成功解析 5 条学术论文结构化数据。
2026-09-22 14:10:02 [INFO] academic_pipeline.main - 开始进行数据增量去重校验...
2026-09-22 14:10:02 [INFO] academic_pipeline.main - [放行] 论文 2401.00001v1 为增量数据，准备写入。
2026-09-22 14:10:02 [INFO] academic_pipeline.main - 正在批量写入 5 条新增记录至数据库...
2026-09-22 14:10:02 [INFO] academic_pipeline.main - 批量写入完成。
2026-09-22 14:10:02 [INFO] utils.redis_client - Redis 去重客户端连接已安全释放。
2026-09-22 14:10:02 [INFO] academic_pipeline.main - === 学术数据管道任务执行完毕，所有资源已安全释放 ===

```

---

## 🤝 许可证 (License)

本项目采用 [MIT License](https://www.google.com/search?q=LICENSE&utm_source=gemini) 开源许可证。

```

```