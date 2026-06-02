

## 第四步：把一次调试记录整理成短错因卡片

求助结束后，如果这次是一次完整 debug，可以把它整理成一张很短的错因卡片。

注意：这个卡片不是给学生长篇阅读用的。它主要有两个用途：

1. 后面生成复习资料；
2. 后面自动出考试题。

调用：

```python
from llm import summarize_error_record

card = summarize_error_record(archive_item)
```

其中 `archive_item` 还是前面建议保存的那种完整调试记录，例如包含题目、代码、输入输出、OJ 结果、诊断结果等。

返回值大致如下：

```python
{
    "title": "一句话标题",
    "error_type": "错误类型",
    "root_cause": "根本原因",
    "knowledge_points": ["知识点"],
    "wrong_code_pattern": "错误代码模式",
    "exam_focus": "后续出题应该重点考什么",
    "priority": "high"
}
```

前端展示时，其实只展示 `title`、`root_cause`、`knowledge_points` 就差不多了。  
`exam_focus` 更主要是给后面的自动出题用的。

### `summarize_error_record` 参数

```python
summarize_error_record(
    archive_item,
    api_key=api_key,
    url=url,
    model_name="deepseek-v4-pro",
    thinking="enabled"
)
```

| 参数 | 含义 |
|---|---|
| `archive_item` | 一次完整调试归档记录 |
| `api_key` | API Key |
| `url` | API 地址 |
| `model_name` | 模型名，默认用 pro |
| `thinking` | 是否开启思考模式。这个任务不算特别难，但默认开着也没坏处 |

---

## 第五步：根据历史错因生成复习资料

如果已经有一些错因卡片，就可以生成复习资料。

这里不是让 AI 写一本讲义。  
真正有用的是：把几十条甚至上百条错因按知识点聚类，然后告诉用户哪些地方最应该复习、哪些地方适合出题考。

调用：

```python
from llm import generate_review_material

review = generate_review_material(
    error_cards=error_cards,
    archive_items=archive_items,
    review_goal="期末复习",
    user_prompt="稍微多关注递归和边界情况"
)
```

`error_cards` 是错因卡片列表，建议传。  
`archive_items` 是原始调试记录列表，可以传，也可以不传。传了会更具体，但是 prompt 也会更长。

返回值大致如下：

```python
{
    "title": "复习标题",
    "summary": "总复习建议",
    "review_by_knowledge_point": [
        {
            "knowledge_point": "知识点",
            "priority": "high",
            "what_to_review": "复习什么",
            "how_to_test": "适合怎样考核"
        }
    ],
    "recommended_exam_mix": {
        "short_blank": "短代码补全适合考什么",
        "long_blank": "长代码补全适合考什么",
        "rewrite": "从零重写适合考什么"
    },
    "_analysis": {}
}
```

其中 `_analysis` 是更原始的知识点聚类结果。  
如果前端不想展示，可以直接忽略。

### `generate_review_material` 参数

```python
generate_review_material(
    error_cards=None,
    archive_items=None,
    review_goal="期末复习",
    user_prompt="",
    max_items=120,
    api_key=api_key,
    url=url,
    model_name="deepseek-v4-pro",
    thinking="enabled"
)
```

| 参数 | 含义 |
|---|---|
| `error_cards` | 错因卡片列表，建议传 |
| `archive_items` | 原始调试记录列表，可选 |
| `review_goal` | 复习目标，例如“期末复习” |
| `user_prompt` | 用户额外要求，例如“不要考 KMP”“难一点但别太难” |
| `max_items` | 最多送入多少条历史记录 |
| `api_key` | API Key |
| `url` | API 地址 |
| `model_name` | 模型名，默认 pro |
| `thinking` | 是否开启思考模式，默认开启 |

---

## 第六步：生成一套考核题


这个才是复习模块里比较重要的部分。

用户不是只能生成一道题，而是可以决定三类题分别生成几道：

1. `short_blank`：短代码补全，比如补一行；
2. `long_blank`：长代码补全，比如补一个函数、一个循环体；
3. `rewrite`：从零开始重写。

调用：

```python
from llm import generate_exam_paper

paper = generate_exam_paper(
    error_cards=error_cards,
    archive_items=archive_items,
    short_blank_count=2,
    long_blank_count=1,
    rewrite_count=1,
    user_prompt="稍微难点，但不要考 KMP，这个我已经掌握了"
)
```

这个函数内部会做两步：

第一步，先整体规划这张卷子。  
第二步，多线程并行生成每一道题。

返回值大致如下：

```python
{
    "paper_plan": {
        "paper_title": "试卷标题",
        "paper_goal": "这张卷子想考什么",
        "question_specs": []
    },
    "questions": [
        {
            "qid": 1,
            "question_type": "short_blank",
            "language": "python",
            "title": "题目标题",
            "tested_knowledge_points": ["知识点"],
            "user_view": {
                "problem_statement": "给用户看的题面",
                "code_template": "给用户看的代码模板",
                "submit_instruction": "提交说明"
            },
            "standard_code": "后台标准答案代码",
            "hidden_tests": [
                {"input": "隐藏测试输入"}
            ]
        }
    ]
}
```

注意：

`user_view` 是可以展示给用户的。  
`standard_code` 不能展示给用户。  
`hidden_tests` 也不能展示给用户。  
`hidden_tests` 里只有输入，没有输出。标准输出应该由运行模块拿 `standard_code` 自己跑出来。

也就是说，真正提交时大概是：

```text
用户提交代码
→ 运行模块拿 hidden_tests 跑用户代码
→ 运行模块拿 standard_code 跑标准答案
→ 比较输出
→ 返回 AC / WA / RE / TLE
```

这一部分需要辛苦负责“运行程序”功能的同学做一下。

### `generate_exam_paper` 参数

```python
generate_exam_paper(
    error_cards=None,
    archive_items=None,
    short_blank_count=2,
    long_blank_count=1,
    rewrite_count=1,
    language="python",
    difficulty="auto",
    user_prompt="",
    hidden_test_count=6,
    max_workers=4,
    api_key=api_key,
    url=url,
    plan_model_name="deepseek-v4-pro",
    question_model_name="deepseek-v4-pro",
    thinking="enabled"
)
```

| 参数 | 含义 |
|---|---|
| `error_cards` | 错因卡片列表，建议传 |
| `archive_items` | 原始调试记录列表，可选 |
| `short_blank_count` | 短代码补全题数量 |
| `long_blank_count` | 长代码补全题数量 |
| `rewrite_count` | 从零重写题数量 |
| `language` | 题目语言，默认 python |
| `difficulty` | 难度，默认 auto |
| `user_prompt` | 用户额外出题要求 |
| `hidden_test_count` | 每道题生成几个隐藏输入 |
| `max_workers` | 并行生成题目的线程数 |
| `api_key` | API Key |
| `url` | API 地址 |
| `plan_model_name` | 规划整张卷子的模型 |
| `question_model_name` | 生成单道题的模型 |
| `thinking` | 是否开启思考模式，默认开启（特别警告：如果开启，这里可能会非常慢！目前我暂时还没能修复这个问题，暂时建议默认不开启，但交给用户选择） |

---

