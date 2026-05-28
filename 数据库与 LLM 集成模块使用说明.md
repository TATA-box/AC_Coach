# 数据库与 LLM 集成模块使用说明

## 一、模块概述

本模块提供两个核心类：
- `Database`：SQLite 数据库操作，管理题目、代码记录、诊断记录、引导步骤、错因库
- `LLMIntegration`：封装 LLM 调用与数据库存储的对接逻辑，简化 AI 分析与诊断流程

---

## 二、Database 类方法说明

### 2.1 题目管理

| 方法                               | 功能                   | 返回值                            |
| ---------------------------------- | ---------------------- | --------------------------------- |
| `add_problem(title, content, ...)` | 添加题目（含分析结果） | `problem_id`                      |
| `get_all_problems()`               | 获取所有题目列表       | `[{"id", "title", "created_at"}]` |
| `get_problem(problem_id)`          | 获取单个题目完整信息   | `dict` 或 `None`                  |

### 2.2 代码记录管理

| 方法                                             | 功能             | 返回值      |
| ------------------------------------------------ | ---------------- | ----------- |
| `add_code_record(problem_id, code, language)`    | 保存代码快照     | `record_id` |
| `update_code_result(record_id, output, success)` | 更新代码运行结果 | 无          |

### 2.3 诊断记录管理

| 方法                                   | 功能                   | 返回值         |
| -------------------------------------- | ---------------------- | -------------- |
| `add_diagnosis(...)`                   | 创建诊断记录           | `diagnosis_id` |
| `update_diagnosis(...)`                | 更新诊断详细信息       | 无             |
| `get_diagnoses_by_problem(problem_id)` | 获取某题的所有诊断记录 | `[dict]`       |

### 2.4 引导步骤管理

| 方法                                                       | 功能                     | 返回值    |
| ---------------------------------------------------------- | ------------------------ | --------- |
| `add_guide_step(diagnosis_id, step_no, title, guide, ...)` | 保存单步引导             | `step_id` |
| `get_guide_steps(diagnosis_id)`                            | 获取某诊断的所有引导步骤 | `[dict]`  |

### 2.5 错因库管理

| 方法                                                     | 功能                           | 返回值       |
| -------------------------------------------------------- | ------------------------------ | ------------ |
| `add_mistake(problem_id, diagnosis_id, error_type, ...)` | 添加错因记录                   | `mistake_id` |
| `get_all_mistakes(include_mastered)`                     | 获取所有错因（可选排除已掌握） | `[dict]`     |
| `mark_mistake_mastered(mistake_id, mastered)`            | 标记错因为已掌握/未掌握        | 无           |

---

## 三、LLMIntegration 类方法说明

### 3.1 `analyze_and_save_problem(problem_text, title)`

**功能**：调用 AI 分析题目（结构化题面 + 题目分析），并将结果存入数据库。

**参数**：
| 参数           | 必填 | 说明                                             |
| -------------- | ---- | ------------------------------------------------ |
| `problem_text` | ✅    | 题目原文                                         |
| `title`        |      | 题目标题（可选，若不提供则自动从分析结果中获取） |

**返回值**：`(problem_id, analysis, problem_struct)`
- `problem_id`：数据库中的题目 ID
- `analysis`：`analyze_problem` 返回的字典（知识点、难度等）
- `problem_struct`：`structure_problem_text` 返回的结构化题面

### 3.2 `diagnose_and_save(problem_id, problem_text, problem_analysis, code, ...)`

**功能**：调用 AI 进行代码诊断（自动选择 debug 或 next_hint 模式），保存诊断记录和引导步骤。

**参数**：
| 参数               | 必填 | 说明                                      |
| ------------------ | ---- | ----------------------------------------- |
| `problem_id`       | ✅    | 题目 ID                                   |
| `problem_text`     | ✅    | 题目原文                                  |
| `problem_analysis` | ✅    | `analyze_and_save_problem` 返回的分析结果 |
| `code`             | ✅    | 学生代码                                  |
| `program_output`   |      | 程序实际输出                              |
| `expected_output`  |      | 期望输出                                  |
| `error_message`    |      | 编译/运行错误信息                         |
| `oj_result`        |      | OJ 结果（WA/RE/TLE 等）                   |
| `extra_info`       |      | 学生补充描述                              |

**返回值**：`(diagnosis_id, mode, diagnosis_dict, steps)`
- `diagnosis_id`：诊断记录 ID
- `mode`：`"debug"` 或 `"next_hint"`
- `diagnosis_dict`：诊断结果（debug 模式下有值）
- `steps`：引导步骤列表

**step 结构**：
```json
{
    "step_no": 1,
    "title": "观察程序输出",
    "guide": "程序输出 -1，但期望输出 3",
    "start_line": 2,
    "end_line": 2,
    "student_question": "检查第2行的运算符",
    "expected_discovery": "应该用加法而不是减法",
    "focus": "算术运算"
}
```

## 四、使用示例

python

```
from database import Database
from llm_integration import LLMIntegration

# 初始化
db = Database("accoach.db")
llm = LLMIntegration(db)

# 1. 添加题目
problem_text = "输入两个整数 a 和 b，输出它们的和。"
problem_id, analysis, _ = llm.analyze_and_save_problem(problem_text, "求和问题")

# 2. 诊断代码
wrong_code = "a, b = map(int, input().split())\nprint(a - b)"
diagnosis_id, mode, diagnosis_dict, steps = llm.diagnose_and_save(
    problem_id=problem_id,
    problem_text=problem_text,
    problem_analysis=analysis,
    code=wrong_code,
    program_output="-1",
    expected_output="3",
    extra_info="输出和预期不符"
)

# 3. 显示引导步骤
for step in steps:
    print(f"步骤{step['step_no']}: {step['title']}")
    print(f"  {step['guide']}")
```



------

## 五、数据库表结构

| 表名              | 用途                             |
| :---------------- | :------------------------------- |
| `problems`        | 题目信息 + 分析结果 + 结构化题面 |
| `code_records`    | 代码快照 + 运行结果              |
| `diagnoses`       | AI 诊断记录                      |
| `guide_steps`     | 分步引导内容                     |
| `mistake_library` | 错因库 + 错因卡片                |

------

## 六、注意事项

1. **API Key**：请确保 `llm.py` 中的 `api_key` 配置正确且网络可访问 DeepSeek API
2. **线程安全**：`start_auto_coach_session` 内部使用后台线程，不要在 Qt 主线程中长时间等待 `next_step()`
3. **数据库文件**：默认使用 `accoach.db`，可通过 `Database(db_path)` 自定义路径
4. **JSON 字段**：部分字段（如 `knowledge_points`、`suspected_locations`）在数据库中存储为 JSON 字符串，读写时需使用 `json.dumps()` / `json.loads()`