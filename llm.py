import json
import re
import queue
import threading
from openai import OpenAI

api_key = "sk-c0547d19dd04413690a8191d3ee3f2cd"
url = "https://api.deepseek.com"

STEP_RE = re.compile(r"<step>\s*([\s\S]*?)\s*</step>", re.I)


def get_client(api_key=api_key, url=url):
    return OpenAI(api_key=api_key, base_url=url,timeout=60)


def extract_json(text):
    text = (text or "").strip()
    text = re.sub(r"^```json", "", text)
    text = re.sub(r"^```", "", text)
    text = re.sub(r"```$", "", text).strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        m = re.search(r"\{[\s\S]*\}", text)
        if m:
            return json.loads(m.group())
    raise ValueError("模型返回内容不是合法 JSON")


def thinking_body(thinking):
    if thinking == "enabled":
        return {"thinking": {"type": "enabled"}}
    if thinking == "disabled":
        return {"thinking": {"type": "disabled"}}
    if isinstance(thinking, dict):
        return {"thinking": thinking}
    return None


def call_json(system_prompt, user_prompt, model_name="deepseek-v4-flash", max_tokens=4096,thinking="disabled", api_key=api_key, url=url):
    try:
        r = get_client(api_key, url).chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": system_prompt.strip()},
                {"role": "user", "content": user_prompt.strip()},
            ],
            response_format={"type": "json_object"},
            max_tokens=max_tokens,
            stream=False,
            extra_body=thinking_body(thinking),
        )
        return extract_json(r.choices[0].message.content)
    except Exception as e:
        raise RuntimeError(f"调用 LLM 失败：{e}") from e


def stream_content(system_prompt, user_prompt, model_name="deepseek-v4-flash", max_tokens=4096,thinking="disabled", api_key=api_key, url=url):
    try:
        s = get_client(api_key, url).chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": system_prompt.strip()},
                {"role": "user", "content": user_prompt.strip()},
            ],
            max_tokens=max_tokens,
            stream=True,
            extra_body=thinking_body(thinking),
        )
        for chunk in s:
            if not chunk.choices:
                continue
            text = getattr(chunk.choices[0].delta, "content", None)
            if text:
                yield text
    except Exception as e:
        raise RuntimeError(f"流式调用 LLM 失败：{e}") from e


class GuideScriptIterator:
    def __init__(self, steps):
        self.steps = steps or []
        self.index = 0
    def __iter__(self):
        return self
    def __next__(self):
        if self.index >= len(self.steps):
            raise StopIteration
        step = self.steps[self.index]
        self.index += 1
        return step
    def reset(self):
        self.index = 0
    def to_list(self):
        return self.steps[:]


class DebugDiagnosis:
    def __init__(self, raw):
        self.raw = raw or {}
        self.has_error = self.raw.get("has_error", "uncertain")
        self.error_summary = self.raw.get("error_summary", "")
        self.error_type = self.raw.get("error_type", "")
        self.knowledge_points = self.raw.get("knowledge_points", [])
        self.suspected_locations = self.raw.get("suspected_locations", [])
        self.confidence = self.raw.get("confidence", "medium")
        self.reason_for_uncertainty = self.raw.get("reason_for_uncertainty", "")
        self.debug_suggestion = self.raw.get("debug_suggestion", "")
        self.guide = GuideScriptIterator(self.raw.get("guide_steps", []))
    def to_dict(self, include_guide_steps=True):
        d = {
            "has_error": self.has_error,
            "error_summary": self.error_summary,
            "error_type": self.error_type,
            "knowledge_points": self.knowledge_points,
            "suspected_locations": self.suspected_locations,
            "confidence": self.confidence,
            "reason_for_uncertainty": self.reason_for_uncertainty,
            "debug_suggestion": self.debug_suggestion,
        }
        if include_guide_steps:
            d["guide_steps"] = self.guide.to_list()
        return d

def add_line_numbers(code):
    if not code:
        return ""
    return "\n".join(f"{i:>4}: {line}" for i, line in enumerate(code.splitlines(), 1))

def cut(text, max_len=8000):
    if text is None:
        return ""
    return text if len(text) <= max_len else text[:max_len] + "\n\n[内容过长，后面部分已省略]"

def build_context(problem_text=None, code=None, program_input=None, program_output=None,expected_output=None, error_message=None, oj_result=None,test_cases=None, extra_info=None, problem_analysis=None):
    return {
        "problem_text": cut(problem_text),
        "problem_analysis": problem_analysis or {},
        "code_with_line_numbers": cut(add_line_numbers(code), 12000),
        "program_input": cut(program_input),
        "program_output": cut(program_output),
        "expected_output": cut(expected_output),
        "error_message": cut(error_message),
        "oj_result": cut(oj_result),
        "test_cases": test_cases or [],
        "extra_info": cut(extra_info),
    }


def normalize_three(x, default):
    if x is None:
        return default[:]
    if isinstance(x, str) or isinstance(x, dict):
        return [x, x, x]
    x = list(x)
    if not x:
        return default[:]
    while len(x) < 3:
        x.append(x[-1])
    return x[:3]

def _norm_problem_text(s):
    return (s or "").replace("\r\n", "\n").replace("\r", "\n")


def _collect_problem_text_fields(x, path=""):
    items = []
    if isinstance(x, str):
        items.append((path, x))
    elif isinstance(x, list):
        for i, v in enumerate(x):
            items += _collect_problem_text_fields(v, f"{path}[{i}]")
    elif isinstance(x, dict):
        for k, v in x.items():
            if str(k).startswith("_"):
                continue
            items += _collect_problem_text_fields(v, f"{path}.{k}" if path else str(k))
    return items


def validate_structured_problem(problem_text, data):
    raw = _norm_problem_text(problem_text)
    errors = []
    if not isinstance(data, dict):
        return False, ["返回值不是 dict"]

    for key in ["title", "background", "description", "input_description", "output_description", "samples", "notes", "other"]:
        if key not in data:
            errors.append(f"缺少字段：{key}")

    for path, value in _collect_problem_text_fields(data):
        v = _norm_problem_text(value)
        if not v.strip():
            continue
        if v not in raw:
            errors.append(f"{path} 不是题目原文中的原样片段")

    if not isinstance(data.get("samples", []), list):
        errors.append("samples 不是 list")
    else:
        for i, s in enumerate(data.get("samples", [])):
            if not isinstance(s, dict):
                errors.append(f"samples[{i}] 不是 dict")
                continue
            for key in ["input", "output", "explanation"]:
                if key not in s:
                    errors.append(f"samples[{i}] 缺少字段：{key}")

    return len(errors) == 0, errors


def structure_problem_text(problem_text, api_key=api_key, url=url, model_name="deepseek-v4-flash", thinking="disabled", max_retries=3):
    system = """
你是程序设计题目的题面切分助手。
任务：把用户提供的算法题题面切分成结构化 JSON。
非常重要：
1. 所有展示给用户的字段，必须逐字复制题目原文中的内容。
2. 不能改写，不能总结，不能润色，不能补充。
3. 如果某一部分原文不存在，就填空字符串 "" 或空列表 []。
4. 样例输入和样例输出也必须逐字复制原文，不要改空格，不要改换行，不要加 Markdown。
5. 如果题目没有背景故事，background 填 ""。
6. notes 用来放提示、说明、数据范围等没有归入前面字段的原文内容。
7. other 用来放仍然无法归类但需要保留的原文片段。
严格返回 JSON：
{
  "title": "题目标题，若没有则为空字符串",
  "background": "题目背景故事，若没有则为空字符串",
  "description": "题目描述",
  "input_description": "输入描述",
  "output_description": "输出描述",
  "samples": [
    {
      "input": "样例输入",
      "output": "样例输出",
      "explanation": "样例解释，若没有则为空字符串"
    }
  ],
  "notes": "提示、说明、数据范围等",
  "other": "其他需要保留的原文"
}
"""
    feedback = ""
    last_data = None
    last_errors = []

    for i in range(max_retries):
        user = f"""
请切分下面这道题目。注意：所有字段必须逐字复制原文，不允许改写。

{feedback}

【题目原文】
{problem_text}
"""
        try:
            data = call_json(system, user, model_name=model_name, max_tokens=4096,thinking=thinking, api_key=api_key, url=url)
        except Exception as e:
            last_errors = [str(e)]
            continue

        for key in ["title", "background", "description", "input_description", "output_description", "notes", "other"]:
            data.setdefault(key, "")
        data.setdefault("samples", [])

        ok, errors = validate_structured_problem(problem_text, data)
        last_data = data
        last_errors = errors

        if ok:
            data["_validate_passed"] = True
            data["_validate_errors"] = []
            data["_attempts"] = i + 1
            return data

        feedback = f"""
上一次切分没有通过校验，请根据下面的问题重新切分。
校验失败原因：
{json.dumps(errors, ensure_ascii=False)}

要求：失败字段必须改成题目原文中可以直接找到的原样片段。不能概括，不能改字，不能自己补。
"""

    if last_data is None:
        last_data = {
            "title": "",
            "background": "",
            "description": problem_text,
            "input_description": "",
            "output_description": "",
            "samples": [],
            "notes": "",
            "other": ""
        }

    last_data["_validate_passed"] = False
    last_data["_validate_errors"] = last_errors
    last_data["_attempts"] = max_retries
    return last_data



def analyze_problem(problem_text, api_key=api_key, url=url, model_name="deepseek-v4-flash"):
    system = """
你是“程序设计实习”课程助教，帮助大一学生理解题目，不直接给完整代码。
严格返回 JSON：
{
  "summary": "题目概括",
  "input_format": "输入格式",
  "output_format": "输出格式",
  "knowledge_points": ["知识点"],
  "constraints": ["限制条件"],
  "common_pitfalls": ["常见错误"],
  "suggested_approach": ["解题步骤"],
  "difficulty": "入门/初级/中偏易/中等/中偏难/困难/极难"
}
"""
    user = f"请分析下面这道程序设计题目：\n\n{problem_text}"
    return call_json(system, user, model_name=model_name, max_tokens=2048,thinking="disabled", api_key=api_key, url=url)


def diagnose_error(context, api_key=api_key, url=url, model_name="deepseek-v4-pro", thinking="disabled"):
    system = """
你是“程序设计实习”课程的调试助教，面向大一学生。
任务：判断程序是否可能有错，定位可疑行，解释错误类型和相关知识点。
不要直接给完整正确代码，不要输出隐藏思维链，只输出能展示给学生的内容。
严格返回 JSON：
{
  "has_error": "yes/no/uncertain",
  "error_summary": "一两句话概括问题",
  "error_type": "数组越界/循环边界错误/输出格式错误/状态更新顺序错误/递归出口错误/语法错误/运行时错误/算法思路错误/OJ隐藏用例错误/不确定",
  "knowledge_points": ["知识点"],
  "suspected_locations": [{"start_line": 1, "end_line": 3, "reason": "怀疑原因"}],
  "evidence": ["证据"],
  "confidence": "low/medium/high",
  "reason_for_uncertainty": "信息不足时说明缺什么，否则留空",
  "debug_suggestion": "下一步建议学生检查什么"
}
"""
    user = f"""
请诊断下面这次程序调试信息。

【题目原文】
{context['problem_text']}

【题目分析】
{json.dumps(context['problem_analysis'], ensure_ascii=False)}

【带行号的代码】
{context['code_with_line_numbers']}

【程序输入】
{context['program_input']}

【程序实际输出】
{context['program_output']}

【期望输出】
{context['expected_output']}

【报错信息】
{context['error_message']}

【OJ 结果】
{context['oj_result']}

【测试样例】
{json.dumps(context['test_cases'], ensure_ascii=False)}

【补充信息】
{context['extra_info']}
"""
    return call_json(system, user, model_name=model_name, thinking=thinking,api_key=api_key, url=url)


def review_diagnosis(context, diagnosis, api_key=api_key, url=url, model_name="deepseek-v4-flash", thinking="disabled"):
    system = """
你是“程序设计实习”课程的调试复核助教。
检查上一轮诊断是否和题目、代码、输出、报错相符；如果行号不准或证据不足，请修正。
不要直接给完整正确代码，不要输出隐藏思维链。严格返回和上一轮相同结构的 JSON。
"""
    user = f"""
【原始调试上下文】
{json.dumps(context, ensure_ascii=False)}

【上一轮诊断】
{json.dumps(diagnosis, ensure_ascii=False)}

请复核并给出最终诊断。
"""
    return call_json(system, user, model_name=model_name, thinking=thinking,api_key=api_key, url=url)


def guide_prompt(max_steps=6):
    system = f"""
你是“程序设计实习”课程的调试引导助教。
生成 3 到 {max_steps} 个分步调试引导。每一步要短，适合点击“下一步”展示。
像助教一样引导学生观察，不要直接宣布答案，不要给完整修复代码，不要输出隐藏思维链。
步骤应递进：观察现象 -> 定位可疑代码 -> 比较题意/输出/状态 -> 点明矛盾 -> 总结错因。
每一步 JSON 字段：step_no, title, focus, start_line, end_line, guide, student_question, expected_discovery。
没有明确行号时 start_line 和 end_line 用 null。
"""
    stream_system = system + """
流式输出格式要求：
不要输出 Markdown，不要输出完整 JSON 数组。
每完成一步，立刻输出：<step>{单个步骤 JSON 对象}</step>
"""
    json_system = system + """
严格返回 JSON：{"guide_steps": [步骤对象, 步骤对象]}
"""
    return json_system, stream_system


def normalize_step(step, i):
    step = dict(step)
    step.setdefault("step_no", i)
    step.setdefault("title", f"第 {step['step_no']} 步")
    step.setdefault("focus", "")
    step.setdefault("start_line", None)
    step.setdefault("end_line", None)
    step.setdefault("guide", "")
    step.setdefault("student_question", "")
    step.setdefault("expected_discovery", "")
    return step


def generate_guide_steps(context, diagnosis, api_key=api_key, url=url,model_name="deepseek-v4-flash", thinking="disabled", max_steps=6):
    system, _ = guide_prompt(max_steps)
    user = f"""
请根据下面的调试上下文和最终诊断，生成分步调试引导。

【调试上下文】
{json.dumps(context, ensure_ascii=False)}

【最终诊断】
{json.dumps(diagnosis, ensure_ascii=False)}
"""
    data = call_json(system, user, model_name=model_name, thinking=thinking,api_key=api_key, url=url)
    return [normalize_step(s, i + 1) for i, s in enumerate(data.get("guide_steps", []))]


def generate_guide_steps_stream(context, diagnosis, api_key=api_key, url=url,model_name="deepseek-v4-flash", thinking="disabled", max_steps=6):
    _, system = guide_prompt(max_steps)
    user = f"""
请根据下面的调试上下文和最终诊断，流式生成分步调试引导。
每完成一步就立即输出一个 <step>...</step>。

【调试上下文】
{json.dumps(context, ensure_ascii=False)}

【最终诊断】
{json.dumps(diagnosis, ensure_ascii=False)}
"""
    buf = ""
    count = 0
    for part in stream_content(system, user, model_name=model_name, thinking=thinking,api_key=api_key, url=url):
        buf += part
        while True:
            m = STEP_RE.search(buf)
            if not m:
                break
            buf = buf[m.end():]
            count += 1
            yield normalize_step(json.loads(m.group(1)), count)

    if count == 0:
        data = extract_json(buf)
        for i, step in enumerate(data.get("guide_steps", []), 1):
            yield normalize_step(step, i)


def prepare(problem_text=None, code=None, program_input=None, program_output=None,expected_output=None, error_message=None, oj_result=None, test_cases=None,extra_info=None, problem_analysis=None, auto_analyze_problem=True,api_key=api_key, url=url, model_name=None, thinking=None,problem_model_name="deepseek-v4-flash"):
    models = normalize_three(model_name, ["deepseek-v4-pro", "deepseek-v4-flash", "deepseek-v4-flash"])
    thinkings = normalize_three(thinking, ["disabled", "disabled", "disabled"])

    if not problem_analysis and auto_analyze_problem and problem_text:
        try:
            problem_analysis = analyze_problem(problem_text, api_key, url, problem_model_name)
        except Exception:
            problem_analysis = {}

    context = build_context(problem_text, code, program_input, program_output,expected_output, error_message, oj_result,test_cases, extra_info, problem_analysis)
    first = diagnose_error(context, api_key, url, models[0], thinkings[0])
    final = review_diagnosis(context, first, api_key, url, models[1], thinkings[1])
    return context, final, models, thinkings


def debug_guide_agent_stream(problem_text=None, code=None, program_input=None, program_output=None,expected_output=None, error_message=None, oj_result=None,test_cases=None, extra_info=None, problem_analysis=None,auto_analyze_problem=True, api_key=api_key, url=url,model_name=None, thinking=None, problem_model_name="deepseek-v4-flash",max_guide_steps=6):
    context, diagnosis, models, thinkings = prepare(
        problem_text, code, program_input, program_output, expected_output,
        error_message, oj_result, test_cases, extra_info, problem_analysis,
        auto_analyze_problem, api_key, url, model_name, thinking, problem_model_name
    )
    yield {"type": "diagnosis", "data": diagnosis}

    steps = []
    for step in generate_guide_steps_stream(context, diagnosis, api_key, url, models[2], thinkings[2], max_guide_steps):
        steps.append(step)
        yield {"type": "step", "data": step}

    result = dict(diagnosis)
    result["guide_steps"] = steps
    yield {"type": "done", "data": result}


def debug_guide_agent(problem_text=None, code=None, program_input=None, program_output=None,expected_output=None, error_message=None, oj_result=None,test_cases=None, extra_info=None, problem_analysis=None,auto_analyze_problem=True, api_key=api_key, url=url,model_name=None, thinking=None, problem_model_name="deepseek-v4-flash",max_guide_steps=6):
    context, diagnosis, models, thinkings = prepare(
        problem_text, code, program_input, program_output, expected_output,error_message, oj_result, test_cases, extra_info, problem_analysis,auto_analyze_problem, api_key, url, model_name, thinking, problem_model_name
    )
    steps = generate_guide_steps(context, diagnosis, api_key, url, models[2], thinkings[2], max_guide_steps)
    result = dict(diagnosis)
    result["guide_steps"] = steps
    return DebugDiagnosis(result)


class DebugGuideSession:
    END = object()

    def __init__(self, **kwargs):
        self.kwargs = kwargs
        self.steps = []
        self.events = []
        self.diagnosis = None
        self.result = None
        self.error = None
        self.q = queue.Queue()
        self.finished = threading.Event()
        threading.Thread(target=self.run, daemon=True).start()

    def run(self):
        try:
            for event in debug_guide_agent_stream(**self.kwargs):
                self.events.append(event)
                if event["type"] == "diagnosis":
                    self.diagnosis = event["data"]
                elif event["type"] == "step":
                    self.steps.append(event["data"])
                    self.q.put(event["data"])
                elif event["type"] == "done":
                    self.result = DebugDiagnosis(event["data"])
        except Exception as e:
            self.error = e
            self.q.put(e)
        finally:
            self.finished.set()
            self.q.put(self.END)

    def next_step(self, timeout=None):
        item = self.q.get(timeout=timeout)
        if item is self.END:
            if self.error:
                raise RuntimeError(f"后台生成引导失败：{self.error}") from self.error
            return None
        if isinstance(item, Exception):
            raise RuntimeError(f"后台生成引导失败：{item}") from item
        return item

    def cached_steps(self):
        return self.steps[:]

    def wait(self, timeout=None):
        self.finished.wait(timeout)
        if not self.finished.is_set():
            return None
        if self.error:
            raise RuntimeError(f"后台生成引导失败：{self.error}") from self.error
        return self.result


def start_debug_guide_session(**kwargs):
    return DebugGuideSession(**kwargs)

def prepare_hint_context(problem_text=None, code=None, program_input=None, program_output=None,expected_output=None, error_message=None, oj_result=None, test_cases=None,extra_info=None, problem_analysis=None, auto_analyze_problem=True,api_key=api_key, url=url, problem_model_name="deepseek-v4-flash"):
    if not problem_analysis and auto_analyze_problem and problem_text:
        try:
            problem_analysis = analyze_problem(problem_text, api_key, url, problem_model_name)
        except Exception:
            problem_analysis = {}
    return build_context(problem_text, code, program_input, program_output,expected_output, error_message, oj_result,test_cases, extra_info, problem_analysis)


def analyze_student_need(context, api_key=api_key, url=url, model_name="deepseek-v4-flash", thinking="disabled"):
    system = """
你是“程序设计实习”课程助教系统的路由判断器。
任务：判断学生现在更需要“纠错调试”还是“下一步提示”。
判断标准：
1. 如果代码基本已经写成，有明确报错、输出不对、OJ WA/RE/TLE/CE，优先选择 debug。
2. 如果代码为空、只有框架、明显没写完、存在 TODO/pass/未实现函数，或学生描述自己不知道接下来怎么写，优先选择 next_hint。
3. 如果代码虽然不完整但已经有具体错误信息，也要判断这个错误是不是因为“还没写完”。没写完则 next_hint，写完后出错则 debug。
4. 不要评价学生水平，不要给解法。
严格返回 JSON：
{
  "code_state": "empty/incomplete/mostly_complete/complete/uncertain",
  "need_type": "debug/next_hint/uncertain",
  "reason": "判断理由",
  "missing_parts": ["如果没写完，缺什么"],
  "debug_evidence": ["如果适合纠错，有哪些证据"],
  "confidence": "low/medium/high"
}
"""
    user = f"""
请判断下面这次求助应该进入哪种模式。

【题目原文】
{context['problem_text']}

【题目分析】
{json.dumps(context['problem_analysis'], ensure_ascii=False)}

【带行号的代码】
{context['code_with_line_numbers']}

【程序输入】
{context['program_input']}

【程序实际输出】
{context['program_output']}

【期望输出】
{context['expected_output']}

【报错信息】
{context['error_message']}

【OJ 结果】
{context['oj_result']}

【测试样例】
{json.dumps(context['test_cases'], ensure_ascii=False)}

【补充信息】
{context['extra_info']}
"""
    data = call_json(system, user, model_name=model_name, max_tokens=1024,thinking=thinking, api_key=api_key, url=url)
    if data.get("need_type") not in ("debug", "next_hint", "uncertain"):
        data["need_type"] = "uncertain"
    return data


def generate_next_hint_step(context, need_analysis=None, hint_history=None, api_key=api_key, url=url, model_name="deepseek-v4-flash", thinking="disabled"):
    system = """
你是“程序设计实习”课程助教，学生现在还没有到适合纠错的阶段，需要一个“下一步提示”。
你只能给一个很小的下一步提示，不能给完整解题路线，不能给一串阶梯提示，不能直接通向最终答案。
提示应该让学生接下来只做一件事，例如：补完一个函数、确认一个变量含义、画一个状态变化表、检查一条输入输出规则、先实现一个最小版本。
不要写完整代码，不要写伪代码模板，不要列出完整算法步骤，不要提前透露后续所有思路。
严格返回 JSON：
{
  "step_no": 1,
  "title": "短标题",
  "focus": "这一步只关注什么",
  "start_line": null,
  "end_line": null,
  "guide": "展示给学生看的下一步提示",
  "student_question": "问学生的一个问题",
  "expected_discovery": "学生完成这一步后应该发现什么",
  "what_to_try_next": "学生现在应该动手做的一件小事"
}
"""
    user = f"""
请只生成一个下一步提示。

【路由判断】
{json.dumps(need_analysis or {}, ensure_ascii=False)}

【已经给过的提示】
{json.dumps(hint_history or [], ensure_ascii=False)}

【题目原文】
{context['problem_text']}

【题目分析】
{json.dumps(context['problem_analysis'], ensure_ascii=False)}

【带行号的代码】
{context['code_with_line_numbers']}

【程序输入】
{context['program_input']}

【程序实际输出】
{context['program_output']}

【期望输出】
{context['expected_output']}

【报错信息】
{context['error_message']}

【OJ 结果】
{context['oj_result']}

【测试样例】
{json.dumps(context['test_cases'], ensure_ascii=False)}

【补充信息】
{context['extra_info']}
"""
    step = call_json(system, user, model_name=model_name, max_tokens=1024,thinking=thinking, api_key=api_key, url=url)
    step = normalize_step(step, len(hint_history or []) + 1)
    step.setdefault("what_to_try_next", "")
    return step


def summarize_error_record(archive_item, api_key=api_key, url=url, model_name="deepseek-v4-flash", thinking="disabled"):
    system = """
你是“程序设计实习”课程的错因整理助教。
任务：把一次调试记录整理成适合放入个人错因库的卡片。
不要给完整正确代码，不要扩展成新的题解。
严格返回 JSON：
{
  "title": "错因卡片标题",
  "error_type": "错误类型",
  "root_cause": "根本原因",
  "wrong_pattern": "学生这次错误的典型模式",
  "knowledge_points": ["相关知识点"],
  "review_question": "复习时可以问自己的问题",
  "review_hint": "复习提示，不直接给答案",
  "avoid_next_time": "下次避免方式",
  "tags": ["标签"],
  "review_priority": "low/medium/high"
}
"""
    user = f"请整理下面这条调试归档记录：\n\n{json.dumps(archive_item, ensure_ascii=False)}"
    return call_json(system, user, model_name=model_name, max_tokens=1536,thinking=thinking, api_key=api_key, url=url)


class NextHintSession:
    def __init__(self, **kwargs):
        self.kwargs = kwargs
        self.hints = []
        self.waiting_for_update = False
        self.context = prepare_hint_context(
            kwargs.get("problem_text"), kwargs.get("code"), kwargs.get("program_input"),
            kwargs.get("program_output"), kwargs.get("expected_output"), kwargs.get("error_message"),
            kwargs.get("oj_result"), kwargs.get("test_cases"), kwargs.get("extra_info"),
            kwargs.get("problem_analysis"), kwargs.get("auto_analyze_problem", True),
            kwargs.get("api_key", api_key), kwargs.get("url", url), kwargs.get("problem_model_name", "deepseek-v4-flash")
        )
        self.need_analysis = kwargs.get("need_analysis")
        if self.need_analysis is None:
            self.need_analysis = analyze_student_need(
                self.context, kwargs.get("api_key", api_key), kwargs.get("url", url),
                kwargs.get("route_model_name", "deepseek-v4-flash"), kwargs.get("thinking", "disabled")
            )

    def next_step(self, timeout=None):
        if self.waiting_for_update:
            return None
        step = generate_next_hint_step(
            self.context, self.need_analysis, self.hints,
            self.kwargs.get("api_key", api_key), self.kwargs.get("url", url),
            self.kwargs.get("hint_model_name", "deepseek-v4-flash"), self.kwargs.get("thinking", "disabled")
        )
        self.hints.append(step)
        self.waiting_for_update = True
        return step

    def update_context(self, **kwargs):
        self.kwargs.update(kwargs)
        self.waiting_for_update = False
        self.context = prepare_hint_context(
            self.kwargs.get("problem_text"), self.kwargs.get("code"), self.kwargs.get("program_input"),
            self.kwargs.get("program_output"), self.kwargs.get("expected_output"), self.kwargs.get("error_message"),
            self.kwargs.get("oj_result"), self.kwargs.get("test_cases"), self.kwargs.get("extra_info"),
            self.kwargs.get("problem_analysis"), self.kwargs.get("auto_analyze_problem", True),
            self.kwargs.get("api_key", api_key), self.kwargs.get("url", url), self.kwargs.get("problem_model_name", "deepseek-v4-flash")
        )
        self.need_analysis = analyze_student_need(
            self.context, self.kwargs.get("api_key", api_key), self.kwargs.get("url", url),
            self.kwargs.get("route_model_name", "deepseek-v4-flash"), self.kwargs.get("thinking", "disabled")
        )

    def cached_steps(self):
        return self.hints[:]

    def wait(self, timeout=None):
        return {"need_analysis": self.need_analysis, "hint_steps": self.hints[:]}


def start_next_hint_session(**kwargs):
    return NextHintSession(**kwargs)


def start_ladder_hint_session(**kwargs):
    return start_next_hint_session(**kwargs)


class AutoCoachSession:
    def __init__(self, **kwargs):
        self.kwargs = kwargs
        self.mode = None
        self.need_analysis = None
        self.session = None
        self.route()

    def base_kwargs(self):
        names = [
            "problem_text", "code", "program_input", "program_output", "expected_output",
            "error_message", "oj_result", "test_cases", "extra_info", "problem_analysis",
            "auto_analyze_problem", "api_key", "url", "model_name", "thinking",
            "problem_model_name", "max_guide_steps"
        ]
        return {name: self.kwargs.get(name) for name in names if name in self.kwargs}

    def route(self):
        base = self.base_kwargs()
        context = prepare_hint_context(
            base.get("problem_text"), base.get("code"), base.get("program_input"),
            base.get("program_output"), base.get("expected_output"), base.get("error_message"),
            base.get("oj_result"), base.get("test_cases"), base.get("extra_info"),
            base.get("problem_analysis"), base.get("auto_analyze_problem", True),
            base.get("api_key", api_key), base.get("url", url), base.get("problem_model_name", "deepseek-v4-flash")
        )
        self.need_analysis = analyze_student_need(
            context, base.get("api_key", api_key), base.get("url", url),
            self.kwargs.get("route_model_name", "deepseek-v4-flash"), self.kwargs.get("route_thinking", "disabled")
        )
        self.mode = self.need_analysis.get("need_type", "uncertain")
        if self.mode == "debug":
            base["problem_analysis"] = context.get("problem_analysis", {})
            base["auto_analyze_problem"] = False
            self.session = start_debug_guide_session(**base)
        else:
            base["problem_analysis"] = context.get("problem_analysis", {})
            base["auto_analyze_problem"] = False
            base["need_analysis"] = self.need_analysis
            base["route_model_name"] = self.kwargs.get("route_model_name", "deepseek-v4-flash")
            base["hint_model_name"] = self.kwargs.get("hint_model_name", "deepseek-v4-flash")
            self.session = start_next_hint_session(**base)
            self.mode = "next_hint"

    def next_step(self, timeout=None):
        return self.session.next_step(timeout)

    def cached_steps(self):
        return self.session.cached_steps()

    def wait(self, timeout=None):
        return self.session.wait(timeout)

    def update_context(self, **kwargs):
        self.kwargs.update(kwargs)
        self.route()


def start_auto_coach_session(**kwargs):
    return AutoCoachSession(**kwargs)

if __name__ == "__main__":
    problem_text = """
给定一个长度为 n 的整数序列，请求出它的最大连续子段和。
1 <= n <= 100000，-10000 <= ai <= 10000
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
    session = start_debug_guide_session(
        problem_text=problem_text,
        code=code,
        oj_result="样例通过，但提交到 OJ 后 WA",
        extra_info="学生说本地样例能过，但 OJ 上显示 Wrong Answer。",
        auto_analyze_problem=False,
    )
    while True:
        step = session.next_step()
        if step is None:
            break
        print(f"第 {step['step_no']} 步：{step['title']}")
        print(step["guide"], "\n")
