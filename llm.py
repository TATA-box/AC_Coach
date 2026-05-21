import json
import re
import queue
import threading
from openai import OpenAI

api_key = "sk-c0547d19dd04413690a8191d3ee3f2cd"
url = "https://api.deepseek.com"

STEP_RE = re.compile(r"<step>\s*([\s\S]*?)\s*</step>", re.I)


def get_client(api_key=api_key, url=url):
    return OpenAI(api_key=api_key, base_url=url)


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