# Reddit Bot Database Schema

This document outlines the schema for the `reddit_interactions` table used by the Reddit bot. The table is designed to log every interaction with a Reddit post, from initial analysis to the final comment posting, including any errors encountered.

---

### 字段说明

| 字段名 | 数据类型 | 描述 |
| :--- | :--- | :--- |
| `id` | `SERIAL` | **主键**: 自增整数，唯一标识每一条记录。 |
| `post_id` | `VARCHAR(20)` | **帖子ID**: Reddit帖子的唯一ID。设有唯一约束，确保每个帖子只记录一次。 |
| `subreddit` | `VARCHAR(100)` | **子版块名称**: 帖子所在的subreddit。 |
| `post_title` | `TEXT` | **帖子标题**: 帖子的完整标题。 |
| `post_content` | `TEXT` | **帖子内容**: 帖子的自述内容（selftext）。 |
| `post_url` | `VARCHAR(512)` | **帖子链接**: 指向Reddit帖子评论区的永久链接。 |
| `post_author` | `VARCHAR(100)` | **帖子作者**: 发布该帖子的Reddit用户名。 |
| `post_created_utc` | `TIMESTAMP WITH TIME ZONE` | **帖子创建时间**: 帖子在Reddit上发布的原始时间（UTC）。 |
| `post_flair` | `VARCHAR(100)` | **帖子Flair**: 帖子的状态标签 (例如, 'Solved', 'Unsolved')，用于判断帖子状态。 |
| `processed_at` | `TIMESTAMP WITH TIME ZONE` | **处理时间**: 机器人最后一次处理该帖子的时间。 |
| `is_relevant` | `BOOLEAN` | **是否相关**: LLM判断该帖子是否为图片处理求助帖。 |
| `llm_analysis_raw` | `TEXT` | **LLM分析原文**: LLM返回的相关性判断原始文本，用于调试。 |
| `generated_comment` | `TEXT` | **生成的评论**: LLM为该帖子生成的评论内容。 |
| `bot_username`      | `VARCHAR(255)` | **主机器人账号**: 运行脚本的主机器人账号。 |
| `commenting_account`| `VARCHAR(255)` | **评论账号**: 成功发布评论的机器人账号。如果未评论，则为NULL。 |
| `comment_failure_count`| `INT` | **评论失败次数**: 机器人尝试评论但失败的次数，默认为0。 |
| `status` | `VARCHAR(50)` | **处理状态**: 记录机器人处理该帖子的最终状态（例如, `COMMENT_POSTED`, `ERROR`, `SKIPPED`）。 |
| `error_message` | `TEXT` | **错误信息**: 如果处理过程中发生错误，此处记录详细的错误信息。 |

### SQL 定义

```sql
CREATE TABLE IF NOT EXISTS reddit_interactions (
    id SERIAL PRIMARY KEY,
    post_id VARCHAR(20) UNIQUE NOT NULL,
    subreddit VARCHAR(100) NOT NULL,
    post_title TEXT,
    post_content TEXT,
    post_url VARCHAR(512) NOT NULL,
    post_author VARCHAR(100),
    post_created_utc TIMESTAMP WITH TIME ZONE,
    post_flair VARCHAR(100),
    processed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    is_relevant BOOLEAN,
    llm_analysis_raw TEXT,
    generated_comment TEXT,
    status VARCHAR(50) NOT NULL,
    error_message TEXT
);

-- 为常用查询字段创建索引，以提升查询性能
CREATE INDEX idx_subreddit ON reddit_interactions(subreddit);
CREATE INDEX idx_post_created_utc ON reddit_interactions(post_created_utc);
CREATE INDEX idx_status ON reddit_interactions(status);

-- 为表和关键列添加注释
COMMENT ON TABLE reddit_interactions IS '用于存储和分析Reddit机器人互动数据的表';
COMMENT ON COLUMN reddit_interactions.id IS '记录的唯一ID';
COMMENT ON COLUMN reddit_interactions.post_id IS 'Reddit帖子的唯一ID';
COMMENT ON COLUMN reddit_interactions.status IS '处理状态 (例如: ''COMMENT_POSTED'', ''SKIPPED_IRRELEVANT'', ''ERROR'')';
