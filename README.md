# 安全文明施工标准化工地管理系统 (Standardized Construction Management System)

学习开发的项目。一个基于 Web 的工程项目信息管理平台，提供项目信息的录入、查询、统计、导入导出等功能。系统集成 OCR 智能识别技术，支持从工程申报表单图片中自动提取项目信息，大幅提升数据录入效率。

## 📋 目录

- [功能特性](#-功能特性)
- [技术栈](#-技术栈)
- [快速开始](#-快速开始)
- [项目结构](#-项目结构)
- [配置说明](#-配置说明)
- [使用说明](#-使用说明)
- [文档](#-文档)
- [许可证](#-许可证)

## ✨ 功能特性

### 核心功能

- **仪表盘**：可视化数据概览，包括统计卡片、图表展示和快捷入口
  - 项目总数、许可证数、待考评项目统计
  - 月度/季度数据统计
  - 状态分布图（饼图）
  - 区域分布图（堆积柱形图/表格）
  - 最近项目列表

- **项目管理**：完整的项目 CRUD 操作
  - 项目列表（搜索、筛选、分页）
  - 项目添加/编辑/查看/删除
  - OCR 智能识别（从表单图片自动提取信息）
  - 批量导入/导出（Excel/CSV）

- **待考评管理**：待考评项目状态筛选与快速操作

- **考评表单**：表单打印与信息展示

- **系统设置**：
  - 数据导出/导入
  - 数据库备份/恢复
  - 自动备份配置

### OCR 智能识别

集成 RapidOCR 引擎，支持从工程申报表单图片中自动识别并提取：
- 项目名称
- 申报企业
- 项目经理
- 项目区域
- 申报时间
- 其他关键信息

## 🛠️ 技术栈

| 组件 | 版本 | 说明 |
|------|------|------|
| Python | 3.7.3+ | 运行环境 |
| Flask | 2.3.3 | Web 框架 |
| Flask-SQLAlchemy | 3.0.5 | ORM 框架 |
| Flask-Login | 0.6.3 | 用户认证 |
| SQLite | 3.x | 数据库 |
| Bootstrap | 5.3.0 | 前端框架 |
| RapidOCR | 1.2.3+ | OCR 引擎 |
| bcrypt | 4.1.2 | 密码加密 |

## 🚀 快速开始

### 系统要求

- 操作系统：UOS / Windows 10+ / Linux / macOS
- CPU 架构：ARM / x86_64
- Python 版本：3.7.3 及以上
- 内存：最低 512MB，推荐 1GB 以上
- 磁盘空间：最低 100MB，推荐 500MB 以上

### 安装步骤

#### 1. 克隆项目

```bash
git clone <repository-url>
cd <project-directory>
```

#### 2. 创建虚拟环境（可选但推荐）

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/macOS
python3 -m venv venv
source venv/bin/activate
```

#### 3. 安装依赖

```bash
pip install -r requirements.txt
```

#### 4. 配置环境变量

复制 `.env` 文件并根据需要修改配置：

```bash
cp .env.example .env  # 如果存在示例文件
```

编辑 `.env` 文件：
```
SENSITIVE_PASSWORD_HASH=<your-password-hash>
SECRET_KEY=<your-secret-key>
```

#### 5. 初始化数据库

首次运行时，系统会自动创建数据库文件。确保 `data` 目录有写入权限。

#### 6. 启动应用

**模块化架构启动方式：**

```bash
# 方式一：使用 Python 模块运行
python -m app

# 方式二：直接运行 app 包
python app/__init__.py

# 方式三：使用 Flask 命令（需设置 FLASK_APP）
export FLASK_APP=app
flask run
```

访问 http://127.0.0.1:5000 即可使用系统。

> **注意**：原 `app.py` 已重构为模块化架构，旧版本备份在 `app_legacy_backup.py`。

## 📁 项目结构

### 重构后的模块化结构

```
.
├── app/                     # 主应用包（模块化架构）
│   ├── __init__.py         # 应用工厂和初始化
│   ├── config/             # 配置模块
│   │   ├── __init__.py
│   │   └── settings.py     # 应用配置类
│   ├── models/             # 数据模型
│   │   ├── __init__.py
│   │   └── project.py      # Project 模型
│   ├── routes/             # 路由蓝图
│   │   ├── __init__.py
│   │   ├── main.py         # 主页和仪表盘路由
│   │   ├── projects.py     # 项目管理路由
│   │   └── auth.py         # 认证路由
│   ├── services/           # 业务逻辑层
│   │   ├── __init__.py
│   │   └── project_service.py  # 项目业务逻辑
│   └── utils/              # 工具函数
│       ├── __init__.py
│       ├── ocr_helper.py   # OCR 辅助函数
│       └── response_helpers.py  # 响应助手
│
├── app_legacy_backup.py    # 原始单文件版本（备份）
├── requirements.txt        # Python 依赖列表
├── .env                    # 环境变量配置
├── .gitignore             # Git 忽略规则
├── LICENSE                # 许可证文件
├── README.md              # 本文件
│
├── data/                  # 数据库目录（运行时创建）
│   └── scms.db           # SQLite 数据库文件
│
├── docs/                  # 项目文档
│   ├── 数据库设计文档.md
│   ├── 程序功能说明文档.md
│   ├── 部署文档.md
│   └── 项目架构设计文档.md
│
├── static/               # 静态资源
│   ├── css/             # 样式文件
│   ├── js/              # JavaScript 文件
│   └── img/             # 图片资源
│
├── templates/            # HTML 模板
│   ├── base.html        # 基础模板
│   ├── dashboard.html   # 仪表盘页面
│   ├── project_list.html # 项目列表页面
│   ├── project_form.html # 项目表单页面
│   ├── pending_list.html # 待考评列表页面
│   ├── evaluation_form.html # 考评表单页面
│   └── settings.html    # 系统设置页面
│
└── uploads/              # 上传文件目录（运行时创建）
```

### 架构说明

- **应用工厂模式**：`app/__init__.py` 中的 `create_app()` 函数负责初始化和配置应用实例
- **蓝图路由**：不同功能模块的路由分离到独立的蓝图中，便于维护和扩展
- **服务层**：业务逻辑封装在 `services` 目录中，实现业务逻辑与路由的分离
- **配置管理**：支持多环境配置，通过 `Config` 类统一管理
- **模型层**：数据库模型集中在 `models` 目录，便于 ORM 管理

## ⚙️ 配置说明

### 环境变量

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| `SECRET_KEY` | Flask 会话密钥 | `project-management-secret-key-2026` |
| `SENSITIVE_PASSWORD_HASH` | 管理员密码哈希（bcrypt） | 必填 |

### 应用配置

在 `app/config/settings.py` 中可修改以下配置：

```python
class Config:
    SQLALCHEMY_DATABASE_URI = 'sqlite:///data/scms.db'  # 数据库连接 URI
    PER_PAGE = 20                                        # 每页显示记录数
    UPLOAD_FOLDER = 'uploads'                            # 上传文件目录
    BACKUP_FOLDER = 'data/backups'                       # 数据库备份目录
    SECRET_KEY = os.environ.get('SECRET_KEY', 'default-key')
```

### 多环境配置

系统支持多环境配置（开发、测试、生产），可通过环境变量切换：

```bash
# 开发环境
export FLASK_ENV=development

# 生产环境
export FLASK_ENV=production
```

## 📖 使用说明

### 登录系统

默认管理员用户名为 `admin`，密码需要在 `.env` 文件中配置 bcrypt 哈希值。

生成密码哈希的方法：
```python
import bcrypt
password = "your_password"
hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
print(hashed.decode('utf-8'))
```

### 主要操作流程

1. **添加项目**
   - 点击"添加项目"按钮
   - 手动填写表单或使用 OCR 识别
   - 提交保存

2. **查询项目**
   - 使用搜索框进行关键词搜索
   - 通过区域、状态下拉框筛选
   - 支持分页浏览

3. **导出数据**
   - 进入"系统设置"
   - 选择导出格式（Excel/CSV）
   - 下载导出文件

4. **数据库备份**
   - 进入"系统设置"
   - 点击"备份数据库"
   - 备份文件保存在 `data/backups` 目录

详细使用说明请参阅 [程序功能说明文档.md](docs/程序功能说明文档.md)

## 📚 文档

- [程序功能说明文档](docs/程序功能说明文档.md) - 详细的功能介绍和操作指南
- [部署文档](docs/部署文档.md) - 完整的部署步骤和配置说明
- [项目架构设计文档](docs/项目架构设计文档.md) - 系统架构和技术设计
- [数据库设计文档](docs/数据库设计文档.md) - 数据库表结构和关系说明

## 🔧 常见问题

### Q: OCR 识别不准确怎么办？
A: 确保上传的图片清晰、无倾斜、光线均匀。支持 JPG、PNG 等常见图片格式。

### Q: 如何修改管理员密码？
A: 使用 bcrypt 生成新的密码哈希，更新 `.env` 文件中的 `SENSITIVE_PASSWORD_HASH` 变量，然后重启应用。

### Q: 数据库文件在哪里？
A: 数据库文件位于 `data/scms.db`，备份文件位于 `data/backups/`。

### Q: 支持哪些浏览器？
A: 推荐使用 Chrome、Firefox、Edge 等现代浏览器的最新版本。

### Q: 重构后如何运行项目？
A: 使用 `python -m app` 或 `python app/__init__.py` 启动应用。原 `app.py` 已备份为 `app_legacy_backup.py`。

### Q: 为什么要进行模块化重构？
A: 模块化架构提高了代码的可维护性、可测试性和可扩展性，便于团队协作和后续功能迭代。

## 📄 许可证

本项目采用 MIT 许可证。详见 [LICENSE](LICENSE) 文件。

## 🤝 贡献

欢迎提交 Issue 和 Pull Request 来帮助改进本项目！

## 📞 技术支持

如有问题或建议，请通过以下方式联系：
- 提交 Issue
- 查看项目文档

---

**注意**：生产环境部署时，请务必修改默认的 `SECRET_KEY` 和密码哈希，以确保系统安全。

**重构说明**：本项目已完成模块化重构，将原 1500+ 行的单文件应用拆分为清晰的模块化架构，提升了代码质量和可维护性。详见 [项目架构设计文档](docs/项目架构设计文档.md)。
