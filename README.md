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

```bash
python app.py
```

访问 http://127.0.0.1:5000 即可使用系统。

## 📁 项目结构

```
.
├── app.py                 # 主应用程序入口
├── requirements.txt       # Python 依赖列表
├── .env                   # 环境变量配置
├── .gitignore            # Git 忽略规则
├── LICENSE               # 许可证文件
├── README.md             # 本文件
├── data/                 # 数据库目录（运行时创建）
│   └── scms.db          # SQLite 数据库文件
├── docs/                 # 项目文档
│   ├── 数据库设计文档.md
│   ├── 程序功能说明文档.md
│   ├── 部署文档.md
│   └── 项目架构设计文档.md
├── static/               # 静态资源
│   ├── css/             # 样式文件
│   ├── js/              # JavaScript 文件
│   └── img/             # 图片资源
├── templates/            # HTML 模板
│   ├── base.html        # 基础模板
│   ├── dashboard.html   # 仪表盘页面
│   ├── project_list.html # 项目列表页面
│   ├── project_form.html # 项目表单页面
│   ├── pending_list.html # 待考评列表页面
│   ├── evaluation_form.html # 考评表单页面
│   └── settings.html    # 系统设置页面
└── uploads/              # 上传文件目录（运行时创建）
```

## ⚙️ 配置说明

### 环境变量

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| `SECRET_KEY` | Flask 会话密钥 | `project-management-secret-key-2026` |
| `SENSITIVE_PASSWORD_HASH` | 管理员密码哈希（bcrypt） | 必填 |

### 应用配置

在 `app.py` 中可修改以下配置：

```python
app.config['SQLALCHEMY_DATABASE_URI']  # 数据库连接 URI
app.config['PER_PAGE']                  # 每页显示记录数（默认 20）
app.config['UPLOAD_FOLDER']             # 上传文件目录（默认 'uploads'）
app.config['BACKUP_FOLDER']             # 数据库备份目录（默认 'data/backups'）
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
