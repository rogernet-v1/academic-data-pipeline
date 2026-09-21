# Academic Data Pipeline (学术文献与开放数据集自动化采集平台)

![Python Version](https://img.shields.io/badge/python-3.10%2B-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![Framework](https://img.shields.io/badge/Framework-Asyncio%20%7C%20httpx%20%7C%20ExecJS-orange.svg)

本项目是一个面向公开学术文献与开放数据集的高性能、高可用自动化采集与 ETL 数据管道系统。针对多源平台接口变动、动态签名鉴权与频率限制等场景，提供高并发异步抓取、动态签名计算、数据对账与增量落库的完整解决方案。

---

## 核心特性 (Key Features)

- ⚡ **高性能异步采集引擎**：基于 `httpx` + `asyncio` 架构，配合自适应并发信号量控制，显著提升吞吐效率。
- 🔐 **动态签名与逆向解密**：集成 `PyExecJS` 动态调用前端混淆签名算法，配合自适应 Token 续期逻辑，突破请求鉴权限制。
- 🛡️ **自适应重试与容错机制**：内置指数退避重试策略，智能识别 HTTP 状态码与业务 Code 码，自动捕获超时与频率限制异常。
- 📊 **数据对账与质量校验**：实现全流程状态追踪，结合源站 `Total` 字段与本地实际入库数量进行自动对账，确保数据零漏采。
- 📝 **结构化日志与追踪**：结合 `Loguru` 建立清晰的运行日志与异常追踪体系，支持日志分级与自动切割存储。

---

## 系统架构与流程 (Architecture)

```text
[源站 API / Web] 
       │
       ▼
[httpx.AsyncClient + 代理池/Headers] ◄── [JS 签名执行模块 (PyExecJS)]
       │
       ▼
[数据校验与对账 (Business Code & Total Check)]
       │
       ▼
[Redis 去重层 (Bloom Filter / Set)] ──► (已存在则跳过)
       │ (新数据)
       ▼
[SQLAlchemy Async ORM] ──► [MySQL / PostgreSQL / Local DB 持久化]