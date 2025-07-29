# Reddit AI 评论机器人

本项目是一个基于 Python 的高级 Reddit 机器人，能够自动搜索帖子、分析内容相关性，并使用多个账户轮流发表由大型语言模型（LLM）生成的评论。

## 主要功能

- **多账户轮询**：支持配置多个 Reddit 账户，并自动轮流使用它们来发表评论，有效分散活动，降低被限制的风险。
- **智能内容分析**：集成 LLM（通过 OpenRouter）来分析帖子标题和内容，判断其是否与预设主题相关。
- **AI 生成评论**：对于相关的帖子，调用 LLM 生成自然、切题的评论内容。
- **数据库持久化**：使用 SQLite 数据库记录所有处理过的帖子及其状态，避免重复评论，并跟踪失败记录。
- **灵活的配置**：所有关键参数，包括 API 密钥、搜索查询、目标 Subreddits 和程序行为，都通过 `config.ini` 文件进行管理。
- **延迟登录**：为了提高效率，只有在需要执行操作时（如发表评论）才登录相应的 Reddit 账户。
- **条件等待**：只有在成功发表评论后，程序才会等待指定的时间间隔，否则将立即处理下一个帖子。
- **“已解决”帖子过滤**：自动跳过带有 “Solved” 标签的帖子。

## 项目结构

```
/reddit-operation
|-- src/
|   |-- main.py             # 应用主入口，负责整体流程控制
|   |-- reddit_client.py    # 封装与 Reddit API 的所有交互
|   |-- llm_client.py       # 封装与 LLM API 的所有交互
|   `-- database_client.py  # 封装与 SQLite 数据库的所有交互
|-- .gitignore              # 指定 Git 应忽略的文件
|-- config.ini              # 存储所有 API 凭证和配置（不应提交到 Git）
|-- requirements.txt        # 项目依赖库
|-- database_schema.md      # 数据库表结构说明
|-- test_reddit_login.py    # 用于测试 Reddit 账户凭据有效性的脚本
`-- README.md               # 本文档
```

## 安装步骤

1.  **克隆仓库**：
    ```bash
    git clone <repository_url>
    cd reddit-operation
    ```

2.  **创建并激活虚拟环境**（推荐）：
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    # 在 Windows 上，使用 `venv\Scripts\activate`
    ```

3.  **安装依赖**：
    ```bash
    pip install -r requirements.txt
    ```

## 配置指南

在运行机器人之前，必须正确配置 `config.ini` 文件。

1.  **配置 Reddit 账户**:
    - **为每个账户创建独立的 Reddit 应用**：登录您的每一个 Reddit 账户，访问 [Reddit 应用偏好设置](https://www.reddit.com/prefs/apps)，点击 “are you a developer? create an app...”，为每个账户创建一个 `script` 类型的应用，以获取其唯一的 `client_id` 和 `client_secret`。
    - **填写凭据**：在 `config.ini` 的 `[reddit]` 部分，将每个账户的 `client_id`, `client_secret`, `user_agent`, `username`, 和 `password` 以**英文逗号**分隔的形式填入。**请确保所有列表的长度都相同！**

2.  **配置 LLM (OpenRouter)**:
    - 在 `[llm]` 部分，填入您的 OpenRouter API 密钥和您想使用的模型名称。

3.  **配置数据库**:
    - 在 `[database]` 部分，指定数据库文件的路径。

4.  **配置搜索和评论行为**:
    - 在 `[reddit]` 部分，设置您的 `search_query`, `subreddits`, `time_filter`, `limit` (每次运行处理的帖子数量), `enable_commenting` (是否开启评论功能), 和 `comment_interval` (成功评论后的等待秒数)。

## 使用方法

### 1. 测试 Reddit 登录

在运行主程序之前，强烈建议先测试所有账户的凭据是否配置正确。

```bash
python3 test_reddit_login.py
```

此脚本将逐一尝试登录 `config.ini` 中配置的所有账户，并报告每个账户的登录状态。

### 2. 运行主程序

确认所有配置无误后，从项目根目录运行主机器人程序。

```bash
python3 src/main.py
```

机器人将开始搜索帖子，分析内容，并根据您的配置进行评论。
