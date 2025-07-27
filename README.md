# Reddit 内容抓取工具

本项目是一个基于 Python 的命令行工具，用于根据指定的关键字、Subreddit 和时间范围在 Reddit 上搜索和抓取帖子。它使用 PRAW (Python Reddit API Wrapper) 库构建。

## 功能特性

- **关键字搜索**：使用一个或多个关键字在多个 Subreddit 中搜索帖子。
- **时间范围过滤**：将搜索结果限制在特定的时间范围内（例如，最近一天、一周、一个月、一年）。
- **自定义输出**：可以指定要检索的帖子 URL 的数量。
- **安全的凭证管理**：API 密钥存储在 `config.ini` 文件中，而不是硬编码在源代码里。
- **模块化和清晰的代码**：项目结构清晰，实现了关注点分离，易于阅读、维护和扩展。

## 项目结构

```
/Reddit
|-- src/
|   |-- __init__.py
|   |-- main.py             # 应用程序的主入口
|   `-- reddit_client.py    # 处理所有与 Reddit API 的交互
|-- .gitignore              # 指定 Git 应忽略的文件
|-- config.ini              # 存储 API 凭证和配置
|-- README.md               # 本文档
`-- requirements.txt        # 列出项目依赖
```

## 安装步骤

1.  **克隆仓库**（或下载源代码）。

2.  **创建虚拟环境**（推荐）：
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```

3.  **安装依赖**：
    ```bash
    pip install -r requirements.txt
    ```

## 配置

在运行本应用前，您需要设置您的 Reddit API 凭证。

1.  **创建 Reddit 应用**：
    - 登录您的 Reddit 账户。
    - 前往 [Reddit 应用偏好设置](https://www.reddit.com/prefs/apps)。
    - 点击 “are you a developer? create an app...”。
    - 填写表单：应用类型选择 `script`，`redirect uri` 填写 `http://localhost:8080`。

2.  **更新 `config.ini` 文件**：
    - 创建应用后，您会得到一个 `client_id`（在应用名称下方）和一个 `client_secret`。
    - 打开项目根目录下的 `config.ini` 文件。
    - 将文件中的占位符替换为您真实的 `client_id` 和 `client_secret`。

    ```ini
    [reddit]
    client_id = YOUR_CLIENT_ID
    client_secret = YOUR_CLIENT_SECRET
    user_agent = Reddit Scraper by MyAwesomeApp v1.0
    ```

## 使用方法

所有的搜索参数都直接定义在 `src/main.py` 文件中。要进行搜索，只需在 `main` 函数中修改这些参数，然后执行脚本即可。

1.  **编辑 `src/main.py`** 来设置您想要的搜索条件：

    ```python
    def main():
        # --- 在这里定义你的搜索参数 ---
        keywords = ["remove person", "sharpen image", "replace background"]
        days_to_search = 10
        results_limit = 15
        subreddits_to_search = "photoshop+postprocessing+photography+PhotoshopRequest"
        # ------------------------------------------

        # ... 剩余代码
    ```

2.  **从项目根目录运行脚本**：

    ```bash
    python3 src/main.py
    ```

脚本将会连接到 Reddit，并打印出符合您所定义条件的帖子的 URL。
