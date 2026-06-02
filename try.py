from llm import analyze_problem, debug_guide_agent, summarize_error_record, generate_review_material, generate_exam_paper

problem_text = "给定一个长度为 n 的整数序列，请求出它的最大连续子段和。\n1 <= n <= 100000\n-10000 <= ai <= 10000"
code = """n=int(input())
a=list(map(int,input().split()))
ans=0
cur=0
for x in a:
    cur=max(0,cur+x)
    ans=max(ans,cur)
    print(ans)"""

pa = analyze_problem(problem_text)
d = debug_guide_agent(problem_text=problem_text, problem_analysis=pa, code=code, program_input="5\n-5 -2 -3 -4 -1", program_output="0", expected_output="-1", oj_result="隐藏用例 WA", auto_analyze_problem=False)
record = {"problem_text": problem_text, "problem_analysis": pa, "code": code, "program_input": "5\n-5 -2 -3 -4 -1", "program_output": "0", "expected_output": "-1", "oj_result": "隐藏用例 WA", "diagnosis": d.to_dict()}
card = summarize_error_record(record)
paper = generate_exam_paper(error_cards=[card], archive_items=[record], short_blank_count=1, long_blank_count=0, rewrite_count=0, user_prompt="题目短一点", max_workers=1)
print("card =", card)
print("questions =", paper["questions"])
print("failed =", paper["failed_questions"])