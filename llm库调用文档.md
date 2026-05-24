# llm库调用文档

下面按照流程来逐步说明要怎么用这个库。

首先说明：请用pip install openai命令按照OpenAI SDK库。然后，在llm.py中，我是用的是我自己的DeepSeek api。**请千万不要泄露这个api，否则会带来一些麻烦**。

关于deepseek api的介绍：deepseek-v4有两个模型：deepseek-v4-flash和deepseek-v4-pro。flash版本便宜、效果相对差；pro版本贵、速度相对慢、效果相对好。

建议：在下文中常常有一个参数：model_name。具体传入什么model_name（到底是...-flash还是...-pro，取决于这个任务的重要程度与困难程度），我个人建议把这个留给使用者选择。默认值可以按照我留的默认参数。

顺便一提：deepseek-v4-flash已经永久一折超级大降价了。deepseek-v4-pro的超级大降价持续到5.31（有可能会延期）。因此在5.31之前无需考虑API成本问题。

---

## 第一步：用户输入题目后，解析题目

解析题目一共有2步。

### step 1:把题目原文切分成结构化题面

```python
from llm import structure_problem_text

problem_struct = structure_problem_text(problem_text,url,api_key)
```

返回值 `problem_struct` 大致结构如下：

```python
{
    "title": "题目标题",
    "background": "题目背景",
    "description": "题目描述",
    "input_description": "输入描述",
    "output_description": "输出描述",
    "samples": [
        {
            "input": "样例输入",
            "output": "样例输出",
            "explanation": "样例解释"
        }
    ],
    "notes": "提示、说明、数据范围等",
    "other": "其他内容",
    "_validate_passed": True,
    "_validate_errors": [],
    "_attempts": 1
}
```

注意：这个函数的目标是切分原文，不是分析题目。所以它会尽量逐字保留原文，不做总结和改写。  

前端展示时一般只展示 `title`、`background`、`description`、`input_description`、`output_description`、`samples`、`notes`、`other`。实际上大部分题目一般都不会全有。如果没有的（None），那么不展示就行了。

如果 `_validate_passed` 是 `False`，说明自动切分不够可靠，可以退回展示原始题面。

总的来说，这个方法就是在整理题干。然后整理好的题干展示给用户。

### step 2：整理题目

这一步的结果不展示给用户，可以在后台开个线程做，没必要让用户等。这一步的核心意图是，减少用户在点击“求助助教”按钮后的等待时间。（提前把题干处理好，之后求助助教时就只需要处理代码，而无需重新思考一遍题干了）

用户把题目加载进系统后，先调用：

```python
from llm import analyze_problem
problem_analysis = analyze_problem(problem_text)
```

返回值 `problem_analysis` 是一个字典，大致结构如下：

```python
{
    "summary": "题目概括",
    "input_format": "输入格式",
    "output_format": "输出格式",
    "knowledge_points": ["知识点"],
    "constraints": ["限制条件"],
    "common_pitfalls": ["常见错误"],
    "suggested_approach": ["解题步骤"],
    "difficulty": "难度"
}
```

建议把它和题目一起保存（可以考虑json格式保存），后面当用户求助助教时直接传入，避免重复分析题目。

### `analyze_problem` 参数

```python
analyze_problem(
    problem_text,
    api_key=api_key,
    url=url,
    model_name="deepseek-v4-flash"
)
```

| 参数 | 含义 | 是否常用 |
|---|---|---|
| `problem_text` | 题目原文 | 必填 |
| `api_key` | API Key，不传则用文件顶部默认值 | 测试的时候不必传 |
| `url` | API 地址，不传则用默认 DeepSeek 地址 | 一般不传，除非不用deepseek |
| `model_name` | 用于题目分析的模型 | 看情况 |

---

## 第二步：用户点击“求助助教”后，自动选择模式并生成提示

说明1：现在有 `start_auto_coach_session`（自动判断） `start_debug_guide_session`（代码已经写完了，进入debug模式）和`start_next_hint_session`（代码没写完，但写不下去了，要下一步的提示）。`start_auto_coach_session`它会先判断学生当前更需要“纠错调试”，还是“下一步提示”。

- 如果代码已经基本写完，但是编译错误、运行错误、输出不对、OJ WA 等，就进入原来的 debug 模式。
- 如果代码还没写完，或者学生只是不知道接下来怎么写，就进入 next_hint 模式，只给一个很小的下一步提示。
- 我的建议：默认状态下用`start_auto_coach_session`。但是要给用户提供选择的余地。即用户可自行选择是哪一种。
- 三个模式的用法几乎相同。下面仅仅以`start_auto_coach_session`为例。有区别的地方会做额外说明。

说明2：为了提速，debug 模式采用“流式输出”。即llm库内部会实时读取从大模型服务器传来的数据，并实时解析数据并传入我封装好的一个迭代器类当中。实际上，下面的session就是一个迭代器。

说明3：下面的函数有相当多的参数。大部分可以不填。建议把其中一些内容的填写交给用户（可自行判断哪些有必要由用户填）

调用：

```python
from llm import start_auto_coach_session

session = start_auto_coach_session(
    problem_text=problem_text,
    problem_analysis=problem_analysis,
    code=student_code,
    program_input=program_input,
    program_output=program_output,
    expected_output=expected_output,
    error_message=error_message,
    oj_result=oj_result,
    extra_info=extra_info,
    auto_analyze_problem=False,
)
```

这个函数会先判断模式，然后自动创建对应的 session。

可以查看当前模式：

```python
print(session.mode)
```

`session.mode` 可能是：

| 值 | 含义 |
|---|---|
| `debug` | 进入分步骤调试模式，即`start_debug_guide_session` |
| `next_hint` | 进入下一步提示模式，即`start_next_hint_session` |

前端点击“下一步”时：

```python
step = session.next_step()

if step is None:
    print("没有更多步骤")
else:
    print(step["title"])
    print(step["guide"])
```

`step` 的结构如下（前提是存在下一步；若不存在，返回None）：

```python
{
    "step_no": 1,
    "title": "短标题",
    "focus": "这一轮关注什么",
    "start_line": 3,
    "end_line": 5,
    "guide": "展示给学生看的引导文字",
    "student_question": "问学生的检查问题",
    "expected_discovery": "学生应该发现什么"
}
```

如果当前是 `next_hint` 模式（即`start_next_hint_session`，注意：**debug模式没有！**），`step` 里还有：

```python
{
    "what_to_try_next": "学生现在应该动手做的一件小事"
}
```

注意：`next_hint` 不是完整题解，也不是一整套提示链。它只会给当前这一小步，避免学生连续点击“下一步”直接看到完整思路。

前端一般需要用到：

| 字段 | 用法 |
|---|---|
| `title` | 显示在步骤标题处 |
| `guide` | 显示在提示气泡或助教面板中 |
| `start_line`, `end_line` | 高亮代码行 |
| `student_question` | 显示为引导问题 |
| `expected_discovery` | 可作为“查看提示/答案”内容 |

### `start_auto_coach_session` 参数

```python
start_auto_coach_session(
    problem_text=None,
    code=None,
    program_input=None,
    program_output=None,
    expected_output=None,
    error_message=None,
    oj_result=None,
    test_cases=None,
    extra_info=None,
    problem_analysis=None,
    auto_analyze_problem=True,
    api_key=api_key,
    url=url,
    model_name=None,
    thinking=None,
    problem_model_name="deepseek-v4-flash",
    max_guide_steps=6,
)
```

| 参数 | 含义 |
|---|---|
| `problem_text` | 题目原文。最好传。 |
| `code` | 学生当前代码。最好传。 |
| `program_input` | 本次运行的输入。默认是`None`。 |
| `program_output` | 学生程序的实际输出。默认是 `None`。 |
| `expected_output` | 期望输出或样例输出。默认是 `None`。 |
| `error_message` | 编译错误、运行时错误等报错信息。默认是 `None`。 |
| `oj_result` | OJ 结果，例如 `WA`、`RE`、`TLE`、`样例通过但隐藏用例错误`。默认 `None` |
| `test_cases` | 测试点列表。默认是 `None`。 |
| `extra_info` | 学生补充描述，例如“样例过了但提交 WA”。 |
| `problem_analysis` | 第一步 `analyze_problem` 的结果。建议传。（建议直接读取之前存好的分析题目的结果） |
| `auto_analyze_problem` | 是否自动分析题目。如果已经传了 `problem_analysis`，请设为 `False`。如果没有传，请设为`True` |
| `api_key` | API Key。 |
| `url` | API 地址。一般不传。 |
| `model_name` | 三轮模型配置。可以不传；也可以传单个模型名或三个模型名列表。下面有详细解释 |
| `thinking` | 三轮 thinking 配置。可传 `"enabled"`、`"disabled"` 或三项列表。下面有详细解释 |
| `problem_model_name` | 第一步自动题目分析用的模型。通常不用管。 |
| `max_guide_steps` | 最多生成多少个引导步骤，默认 6。 |

由于整个求助助教过程的思维链长度是3，因此提供两个调整每步思维链的特征的参数：

`model_name` 含义是：

```python
model_name=[
    "用来诊断错误的模型",
    "用来复核的模型",
    "用来生成引导步骤的模型",
]
```

至于`thinking`参数：
```python
model_name=[
    "诊断错误时要不要深度思考？",
    "复核时要不要深度思考？",
    "生成引导步骤时要不要深度思考？",
]
```

要深度思考传`enabled`，不要深度思考传`disabled`。

模型到底用deepseek-v4-pro还是deepseek-v4-flash，可自行决定。

### `session` 可用方法

| 方法 | 用法 |
|---|---|
| `session.next_step(timeout=None)` | 获取下一个步骤。如果是 debug 模式，就是原来的分步调试；如果是 next_hint 模式，就是一个下一步提示。timeout参数是一个时间限制。即如果多久没有输出就会报错。 |
| `session.cached_steps()` | 获取已经生成并缓存的所有步骤。 |
| `session.wait(timeout=None)` | 等全部生成结束。debug 模式下返回完整 `DebugDiagnosis` 对象。 |
| `session.update_context(...)` | 学生根据提示修改代码后，更新上下文并重新判断应该继续 next_hint 还是切换到 debug。 |

如果当前是 `next_hint` 模式，学生没有修改代码时，再次调用 `next_step()` 可能会返回 `None`。这时应该先让学生根据提示改代码，然后调用：

```python
session.update_context(
    code=new_code,
    program_input=program_input,
    program_output=program_output,
    expected_output=expected_output,
    error_message=error_message,
    oj_result=oj_result,
    extra_info=extra_info,
)
```

Qt 注意：不要在主线程里长时间阻塞调用 `start_auto_coach_session()`、`next_step()` 或 `wait()`。这会导致卡死！


---

## 第三步：求助结束后，归档题目和错误原因

如果这次进入的是 debug 模式，那么生成全部结束后调用：

```python
result = session.wait()
record = result.to_dict()
```

如果这次只是 next_hint 模式，一般不需要立刻归档错因，因为学生还没有经历一次完整调试。可以等学生改完代码、系统切换到 debug 并完成诊断后再归档。

`record` 里包含适合归档的错误信息：

```python
{
    "has_error": "yes",
    "error_summary": "错误概括",
    "error_type": "错误类型",
    "knowledge_points": ["相关知识点"],
    "suspected_locations": [
        {
            "start_line": 3,
            "end_line": 5,
            "reason": "怀疑原因"
        }
    ],
    "confidence": "medium",
    "reason_for_uncertainty": "不确定原因",
    "debug_suggestion": "调试建议",
    "guide_steps": ["分步引导列表"]
}
```

推荐归档这些内容：

```python
archive_item = {
    "problem_text": problem_text,
    "problem_analysis": problem_analysis,
    "code": student_code,
    "program_input": program_input,
    "program_output": program_output,
    "expected_output": expected_output,
    "error_message": error_message,
    "oj_result": oj_result,
    "extra_info": extra_info,
    "diagnosis": result.to_dict(),
}
```

还想生成更适合期末复习的错因卡片，可以继续调用：

```python
from llm import summarize_error_record

error_card = summarize_error_record(archive_item)
```

`error_card` 大致结构如下：

```python
{
    "title": "错因卡片标题",
    "error_type": "错误类型",
    "root_cause": "根本原因",
    "wrong_pattern": "这次错误的典型模式",
    "knowledge_points": ["相关知识点"],
    "review_question": "复习时可以问自己的问题",
    "review_hint": "复习提示",
    "avoid_next_time": "下次避免方式",
    "tags": ["标签"],
    "review_priority": "high"
}
```

建议保存原始 `archive_item`，同时保存 `error_card`。前者用于回看完整调试过程，后者用于期末复习和错因统计。


---

## 另一个可选接口：流式事件模式

如果你们不想用后台 session，而是自己管理线程，可以用：

```python
from llm import debug_guide_agent_stream

for event in debug_guide_agent_stream(...):
    if event["type"] == "diagnosis":
        diagnosis = event["data"]
    elif event["type"] == "step":
        step = event["data"]
    elif event["type"] == "done":
        final_result = event["data"]
```

事件类型：

| 类型 | 含义 |
|---|---|
| `diagnosis` | 初步诊断和复核已经完成。 |
| `step` | 新生成了一个引导步骤，可以立刻展示。 |
| `done` | 全部结束，里面包含完整诊断和所有步骤。 |

这个是我早期写的，其实我认为不如直接用session调用方便。不过还是摆上来吧。

---

## 另一个可选接口：同步模式

如果只是测试，不需要流式展示，可以用：

```python
from llm import debug_guide_agent

diagnosis = debug_guide_agent(
    problem_text=problem_text,
    problem_analysis=problem_analysis,
    code=student_code,
    oj_result="WA",
    auto_analyze_problem=False,
)

print(diagnosis.error_summary)
for step in diagnosis.guide:
    print(step["title"], step["guide"])
```

同步模式会等所有步骤全部生成完才返回，不推荐 GUI 主流程使用。这个单纯只是给我测试用的。实际写QT的时候没必要用这个。

---

## 代码示例

```python

from llm import start_auto_coach_session,structure_problem_text

problem_text = """
给定一个长度为 n 的整数序列，请求出它的最大连续子段和。
1 <= n <= 100000
-10000 <= ai <= 10000
"""

code = """
n = int(input())
a = list(map(int, input().split()))
ans = 0
cur = 0
for x in a:
    cur = max(0, cur + x)
    ans = max(ans, cur)
print(ans)
"""

structured=structure_problem_text(problem_text)
print(structured)

session = start_auto_coach_session(
    problem_text=problem_text,
    code=code,
    oj_result="样例通过，但提交到 OJ 后 WA",
    extra_info="学生说本地样例能过，但 OJ 上显示 Wrong Answer。",
    auto_analyze_problem=False,
    thinking=["disabled","disabled","disabled"]
)

print("当前模式：", session.mode)

while True:
    step = session.next_step()
    if step is None:
        break

    print("=" * 20)
    print(f"第 {step['step_no']} 步：{step['title']}")
    print(step["guide"])
    print("高亮行：", step["start_line"], step["end_line"])

if session.mode == "debug":
    final_result = session.wait()
    print("错误概括：", final_result.error_summary)
    print("错误类型：", final_result.error_type)
```