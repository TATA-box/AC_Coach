# AC Coach

AC Coach 是一个面向程序设计学习场景的简易 IDE。当前版本主要完成了 **Coding 模式**：支持 C++ 文件编辑、编译运行、题目绑定、题面分析，以及基于 DeepSeek API 的 AI 助教提示。`Review` 模式目前作为复习/错因回顾方向的预留页面，后续可以继续扩展。

这份 README 主要给队友看，重点说明：项目能做什么、各模块负责什么、用户操作后代码内部怎么流转。

---

## 1. 当前主要功能

### 1.1 基础 IDE 功能

当前 Coding 模式已经支持：

- 打开项目文件夹；
- 在左侧文件树浏览 `.cpp`、`.c`、`.h`、`.hpp`、`.txt`、`.md` 文件；
- 双击文件后在编辑器中打开；
- 多标签页编辑；
- 新建 `.cpp` 文件；
- 保存当前文件 / 保存所有文件；
- 撤销、重做、剪切、复制、粘贴；
- 使用 `g++` 编译当前 `.cpp` 文件；
- 编译日志输出到底部 `Compile Log`；
- 编译错误 / warning / note 解析到底部 `Problems` 表格；
- 编译成功后弹出外部 `cmd` 窗口运行生成的 `.exe`。

### 1.2 题目绑定与题面分析

每个 `.cpp` 文件可以绑定一道题目。用户通过 `Question -> Modify` 录入或修改题目原文。

保存后，程序会在后台线程中调用 LLM 做两件事：

1. `structure_problem_text()`：把题面拆成标题、背景、描述、输入输出、样例、提示等结构化字段；
2. `analyze_problem()`：分析题目摘要、知识点、限制条件、常见坑点、建议思路和难度。

分析结果会保存到 SQLite 数据库中。之后用户可以通过 `Question -> Check` 查看题目整理结果。

### 1.3 API Key 配置

AI 功能使用 DeepSeek API，URL 固定为：

```text
https://api.deepseek.com
```

用户需要先在菜单中点击 API 配置项，也就是 `act_config` 对应的动作，输入自己的 DeepSeek API Key。

当前实现方式：

- `MainWindow.config_api_key()` 弹出输入框；
- 用户输入 API Key；
- `MainWindow` 使用 `QSettings("AC_coach", "AC_coach")` 保存；
- 保存键名为 `deepseek/api_key`；
- `llm/llm.py` 中的 `get_client()` 每次调用时从 `QSettings` 读取 API Key；
- `CoachController` 不保存 API Key，也不向 `start_auto_coach_session()` 传 API Key。

也就是说，API Key 的保存和检查由 `MainWindow` 管，LLM 调用时由 `llm.py` 自己读取。

### 1.4 AI 助教功能

用户点击 `act_analyse` 后，如果还没有配置 API Key，会先弹窗提醒用户配置。配置完成后，右侧 AI 助教面板会展开。

AI 助教支持三种模式：

| 模式 | 含义 |
| --- | --- |
| 自动判断 | 让 LLM 根据当前代码、报错、输出、题目信息自动判断应该进入纠错调试还是下一步提示 |
| 纠错调试 | 适合代码已经基本写完，但出现编译错误、运行错误、输出不一致、OJ WA 等情况 |
| 下一步提示 | 适合学生还没写完代码，或者不知道接下来该怎么写的情况，只给一个小提示，不直接给完整题解 |

助教面板允许用户补充：

- 程序输入；
- 实际输出；
- 期望输出；
- OJ 结果；
- 额外描述；
- 是否启用深度思考。

LLM 返回的提示会显示在右侧面板中，同时如果返回了 `start_line` 和 `end_line`，编辑器会高亮对应代码行。

---

## 2. 项目结构

```text
AC_coach/
├─ main.py                         # 程序入口
├─ mainwindow.py                   # 主窗口控制中心，负责初始化 UI、Manager、Controller，并连接菜单信号
├─ database.py                     # SQLite 数据库封装
├─ accoach.db                      # 本地 SQLite 数据库文件，运行时会自动创建/更新表结构
├─ pyproject.toml                  # PySide6 Project 配置
│
├─ app/
│  ├─ coach_service.py             # AI 助教控制器，负责右侧助教面板、LLM session、步骤保存和代码高亮
│  ├─ cpp_runner.py                # C++ 编译运行模块，调用 g++，解析编译错误
│  ├─ editor_manager.py            # 编辑器管理模块，负责文件 Tab、保存、编辑操作、代码行高亮
│  ├─ file_manager.py              # 文件读写工具
│  ├─ panel_manager.py             # 底部 Compile Log 和 Problems 面板管理
│  └─ problem_controller.py        # 题目绑定、题面分析、题目查看逻辑
│
├─ ui/
│  ├─ form.ui                      # Qt Designer 设计文件
│  ├─ ui_form.py                   # 由 form.ui 生成的 Python UI 文件
│  └─ coach_panel_ui.py            # 右侧 AI 助教面板的动态 UI 构建代码
│
└─ llm/
   ├─ __init__.py                  # 暴露 LLM 调用入口
   ├─ llm.py                       # LLM 核心逻辑：题面结构化、题目分析、调试、下一步提示
   ├─ llm_integration.py           # 数据库与 LLM 的辅助集成封装，目前主流程主要直接调用 llm.py
   ├─ llm库调用文档.md              # LLM 调用说明文档
   └─ 数据库与 LLM 集成模块使用说明.md
```

---

## 3. 运行环境

当前项目主要依赖：

```text
Python
PySide6
openai
pyqcodeeditor
g++
```

建议安装：

```powershell
pip install PySide6 openai pyqcodeeditor
```

同时需要本机能在命令行直接调用 `g++`。如果是 Windows，需要安装 MinGW / MSYS2 等 C++ 编译环境，并把 `g++` 加入系统 `PATH`。

运行项目：

```powershell
python main.py
```

如果修改了 `ui/form.ui`，需要重新生成 `ui/ui_form.py`：

```powershell
pyside6-uic ui\form.ui -o ui\ui_form.py
```

注意：一般不要手动改 `ui/ui_form.py`，因为它是自动生成文件，重新生成后手动修改会被覆盖。

---

## 4. 核心逻辑链条

### 4.1 程序启动链条

```text
main.py
→ 创建 QApplication
→ 创建 MainWindow
→ Ui_MainWindow.setupUi()
→ 初始化 Database
→ 初始化 EditorManager / PanelManager / CppRunner
→ 初始化 ProblemController / CoachController
→ 读取 QSettings 中保存的 DeepSeek API Key
→ connect_signals()
→ 默认隐藏右侧 AI 面板
→ 显示主窗口
```

对应主要代码：

```text
main.py
mainwindow.py
```

---

### 4.2 打开文件夹和打开文件链条

```text
用户点击 Open Folder
→ MainWindow.openfolder()
→ QFileDialog 选择项目文件夹
→ QFileSystemModel 设置根目录
→ 左侧 projectTree 显示文件树
```

```text
用户双击文件树中的文件
→ MainWindow.openfile()
→ EditorManager.openfile(path)
→ FileManager.readfile(path)
→ 创建 CodeEditor
→ 加载文件内容
→ 加入 editorWidget 的 Tab
```

相关文件：

```text
mainwindow.py
app/editor_manager.py
app/file_manager.py
```

---

### 4.3 新建、保存和编辑链条

```text
用户点击 New
→ MainWindow.new_file_then_modify()
→ EditorManager.createfile()
→ 创建未命名 .cpp Tab
→ 自动进入题目录入流程 ProblemController.modify_current_problem()
```

```text
用户点击 Save / Save All
→ MainWindow.savefile() / MainWindow.saveall()
→ EditorManager.savefile() / EditorManager.saveall()
→ FileManager.writefile()
```

编辑操作：

```text
act_undo / act_redo / act_cut / act_copy / act_paste
→ EditorManager.undo() / redo() / cut() / copy() / paste()
→ 当前编辑器执行对应操作
```

---

### 4.4 编译运行链条

```text
用户点击 Compile & Run
→ MainWindow.compile_run()
→ EditorManager.savefile()
→ 取得当前 .cpp 文件路径
→ PanelManager.clear_all()
→ CppRunner.compile_run(path)
→ QProcess 启动 g++
→ read_stdout() / read_stderr() 收集编译输出
→ compile_finished()
```

如果编译失败：

```text
g++ stderr
→ CppRunner 解析 error / warning / note
→ problems_ready 信号
→ PanelManager.show_problems()
→ Problems 表格显示错误位置和信息
→ run_context_ready 信号
→ CoachController.set_latest_run_context()
→ AI 助教后续可以自动拿到编译错误信息
```

如果编译成功：

```text
Compile succeeded
→ run_context_ready 发出 compile_success
→ QProcess.startDetached()
→ 弹出 cmd 窗口运行 .exe
```

注意：当前 `.exe` 是在外部 `cmd` 中运行，所以程序运行时的标准输出不会自动回填到 IDE 中。AI 助教需要的“实际输出”可以由用户在右侧面板手动填写。

相关文件：

```text
mainwindow.py
app/cpp_runner.py
app/panel_manager.py
app/coach_service.py
```

---

### 4.5 题目录入与分析链条

```text
用户点击 Question -> Modify
→ MainWindow 触发 problem_controller.modify_current_problem()
→ ProblemController.current_cpp_path()
→ 确认当前文件已经保存且是 .cpp
→ ProblemEditDialog 弹窗
→ 用户粘贴题目原文
→ 数据库 add_problem() 或 update_problem()
→ bind_problem_file(path, problem_id)
→ set_problem_analysis_status(problem_id, "analyzing")
→ start_problem_analysis()
```

后台分析线程：

```text
start_problem_analysis()
→ 创建 QThread
→ 创建 ProblemAnalyzeWorker
→ worker.run()
→ structure_problem_text(problem_text)
→ analyze_problem(problem_text)
→ db.update_problem()
→ db.set_problem_analysis_status(problem_id, "done")
→ on_problem_analysis_finished()
```

如果分析失败：

```text
ProblemAnalyzeWorker.failed
→ on_problem_analysis_failed()
→ db.set_problem_analysis_status(problem_id, "failed", error)
→ 弹窗提示用户
```

相关文件：

```text
app/problem_controller.py
database.py
llm/llm.py
```

---

### 4.6 查看题目链条

```text
用户点击 Question -> Check
→ ProblemController.check_current_problem()
→ 根据当前 .cpp 路径查询绑定题目
→ 如果没有绑定，询问是否现在录入
→ 如果正在分析，提示稍后再看
→ 如果分析失败，询问是否重新分析
→ 如果分析完成，format_problem_markdown()
→ ProblemCheckDialog 显示题目整理结果
```

---

### 4.7 API Key 配置链条

```text
用户点击 API 配置菜单项 act_config
→ MainWindow.config_api_key()
→ QInputDialog.getText()
→ 用户输入 DeepSeek API Key
→ self.settings.setValue("deepseek/api_key", key)
→ self.settings.sync()
→ 弹窗提示保存成功
```

AI 功能调用时：

```text
用户点击 act_analyse
→ MainWindow.summon_coach()
→ MainWindow.ensure_api_key()
→ 如果 QSettings 没有 deepseek/api_key，则弹窗提醒配置
→ 如果已有 API Key，则展开右侧 AI 面板
```

LLM 实际调用时：

```text
llm/llm.py
→ get_client()
→ QSettings("AC_coach", "AC_coach")
→ settings.value("deepseek/api_key", "")
→ OpenAI(api_key=api_key, base_url="https://api.deepseek.com", timeout=60)
```

这个设计的好处是：`CoachController` 不需要保存 API Key，也不需要把 API Key 一层一层传下去。

相关文件：

```text
mainwindow.py
llm/llm.py
```

---

### 4.8 AI 助教启动链条

```text
用户点击 act_analyse
→ MainWindow.summon_coach()
→ ensure_api_key()
→ show_ai_panel()
→ CoachController.show_config_page()
→ 右侧显示 AI 助教配置页
```

用户点击“求助助教”：

```text
CoachPanelUI.start_button.clicked
→ CoachController.start_session()
→ collect_context()
```

`collect_context()` 会收集：

```text
当前 .cpp 文件路径
→ 当前文件绑定的题目
→ 题目分析结果
→ 编辑器中的当前代码
→ 用户在助教面板填写的输入输出/OJ/补充信息
→ 最近一次编译错误信息
→ 用户选择的助教模式
→ 是否开启深度思考
```

然后保存数据库记录：

```text
db.ensure_code_record()
→ 保存本次代码和输入输出上下文

db.add_diagnosis()
→ 创建本次助教诊断记录
```

随后在后台线程中启动 LLM：

```text
run_in_thread(task, on_session_started)
→ selected_mode == "debug"
   → start_debug_guide_session(**kwargs)

→ selected_mode == "next_hint"
   → start_next_hint_session(**kwargs)

→ selected_mode == "auto"
   → start_auto_coach_session(**kwargs)
   → LLM 判断最终进入 debug 或 next_hint
```

相关文件：

```text
app/coach_service.py
ui/coach_panel_ui.py
llm/llm.py
database.py
```

---

### 4.9 AI 助教显示下一步链条

Session 启动成功后：

```text
on_session_started()
→ 保存当前 mode
→ db.set_diagnosis_mode_status(status="running")
→ fetch_next_step()
```

读取下一步：

```text
fetch_next_step()
→ 后台线程调用 session.next_step(timeout=120)
→ on_step_received(step)
```

如果拿到了 step：

```text
save_step(step)
→ db.add_guide_step()

render_step(step)
→ 右侧 QTextEdit 显示提示内容
→ 如果 step 有 start_line / end_line
   → EditorManager.highlight_lines(start_line, end_line)
```

如果 step 为 `None`：

```text
debug 模式
→ 说明调试步骤结束
→ finish_debug_session()
→ session.wait()
→ db.update_diagnosis(status="finished")

next_hint 模式
→ 说明当前小提示已经给完
→ 提示用户先修改代码
→ 按钮显示“我已修改，继续”
```

---

### 4.10 next_hint 模式下继续提示链条

`next_hint` 模式不是让学生一直点下一步拿完整题解，而是：

```text
给一个小提示
→ 学生必须先改代码
→ 再继续请求下一步
```

当前实现链条：

```text
用户点击“我已修改，继续”
→ CoachController.update_context_and_fetch()
→ collect_context()
→ 比较 last_context_code 和当前代码
```

如果代码没变：

```text
弹窗提示：
请先根据当前提示修改代码，再点击“我已修改，继续”。
→ 不调用 LLM
```

如果代码变了：

```text
db.update_code_context(code_content=context["code"], ...)
→ 数据库里的 code_records.code_content 更新为当前代码
→ self.last_context_code = context["code"]
→ session.update_context(...)
→ on_context_updated()
→ fetch_next_step()
```

相关文件：

```text
app/coach_service.py
database.py
llm/llm.py
```

---

## 5. 数据库说明

数据库文件默认是项目根目录下的：

```text
accoach.db
```

数据库初始化在 `Database._init_database()` 中完成。如果老数据库缺少新字段，会通过 `_ensure_problem_analysis_columns()` 和 `_ensure_coach_columns()` 自动补字段。

主要表如下：

| 表名 | 用途 |
| --- | --- |
| `problems` | 保存题目原文、题面结构化结果、题目分析结果 |
| `problem_files` | 保存 `.cpp` 文件路径和题目之间的绑定关系 |
| `code_records` | 保存某次代码内容、输入输出、报错、OJ 结果等上下文 |
| `diagnoses` | 保存一次 AI 助教诊断/提示会话 |
| `guide_steps` | 保存 LLM 生成的每一步提示 |
| `mistake_library` | 预留给 Review 模式的错因库 |

---

## 6. 各模块职责

### `main.py`

程序入口。负责创建 `QApplication`、创建并显示 `MainWindow`。

### `mainwindow.py`

主窗口控制中心。负责：

- 初始化 UI；
- 初始化数据库；
- 初始化各个 Manager / Controller；
- 连接菜单、按钮、文件树、编译器信号；
- 切换 Coding / Review 页面；
- 展开和隐藏右侧 AI 面板；
- 配置和检查 API Key。

### `app/editor_manager.py`

编辑器管理模块。负责：

- 创建新文件 Tab；
- 打开已有文件；
- 保存当前文件 / 保存所有文件；
- 关闭文件时检查未保存修改；
- 撤销、重做、剪切、复制、粘贴；
- 获取当前代码；
- 根据 LLM 返回的行号高亮代码。

当前编辑器使用 `pyqcodeeditor` 的 `QCodeEditor`，并启用了 C++ 高亮和补全。

### `app/file_manager.py`

文件读写工具类。只负责实际的 `read_text()` 和 `write_text()`，让 `EditorManager` 不直接处理底层文件读写细节。

### `app/cpp_runner.py`

C++ 编译运行模块。负责：

- 调用 `g++` 编译当前 `.cpp`；
- 收集编译 stdout / stderr；
- 解析 g++ 的 error、warning、note；
- 编译成功后启动外部 cmd 运行 exe；
- 把最近一次编译上下文通过 `run_context_ready` 发给 AI 助教。

### `app/panel_manager.py`

底部面板管理模块。负责：

- 清空 Compile Log 和 Problems；
- 往 Compile Log 追加文字；
- 把编译问题显示到 Problems 表格。

### `app/problem_controller.py`

题目控制模块。负责：

- 当前 `.cpp` 文件和题目之间的绑定；
- 题目录入/修改弹窗；
- 题面分析后台线程；
- 调用 `structure_problem_text()` 和 `analyze_problem()`；
- 查看题目整理结果。

### `app/coach_service.py`

AI 助教控制模块。负责：

- 右侧助教面板的流程控制；
- 收集题目、代码、输入输出、编译错误等上下文；
- 创建或更新 `code_records`；
- 创建 `diagnoses`；
- 启动 `start_auto_coach_session()` / `start_debug_guide_session()` / `start_next_hint_session()`；
- 读取并显示 LLM 返回的 step；
- 保存 `guide_steps`；
- 高亮编辑器中的相关代码行；
- 在 `next_hint` 模式下检查学生是否真的修改了代码。

### `ui/coach_panel_ui.py`

右侧 AI 助教面板的动态 UI。负责构建：

- 助教配置页；
- 助教结果页；
- 模式选择框；
- 深度思考选项；
- 输入输出信息输入框；
- OJ 结果和补充描述输入框；
- 状态文字、提示内容和主操作按钮。

### `llm/llm.py`

LLM 核心模块。负责：

- 从 QSettings 读取 DeepSeek API Key；
- 创建 OpenAI client；
- 题面结构化；
- 题目分析；
- 错误诊断；
- 诊断复核；
- 生成 debug 分步引导；
- 生成 next_hint 小提示；
- 自动判断当前应该进入 debug 还是 next_hint。

主要入口函数：

```text
structure_problem_text()
analyze_problem()
start_auto_coach_session()
start_debug_guide_session()
start_next_hint_session()
```

### `database.py`

SQLite 数据库封装。负责：

- 建表；
- 老数据库字段迁移；
- 题目增删改查；
- 题目和文件绑定；
- 代码记录保存；
- 诊断记录保存；
- 提示步骤保存；
- 错因库预留。

---

## 7. 开发注意事项

### 7.1 不要在代码里写死 API Key

API Key 由用户通过菜单配置，并保存在本机 `QSettings` 中。不要把真实 API Key 写入 `llm.py`、README、数据库或 Git 仓库。

### 7.2 LLM 调用必须放在线程里

LLM 请求可能很慢，不能直接在 Qt 主线程里调用，否则界面会卡死。

当前题目分析使用：

```text
ProblemAnalyzeWorker + QThread
```

当前 AI 助教使用：

```text
FunctionWorker + QThread
```

### 7.3 修改 UI 后要重新生成 `ui_form.py`

如果改了 `ui/form.ui`：

```powershell
pyside6-uic ui\form.ui -o ui\ui_form.py
```

### 7.4 当前运行输出还不能自动捕获

目前编译成功后程序在外部 cmd 里运行，因此标准输入输出不在 IDE 内部托管。后续如果想让 AI 自动拿到运行输出，需要把 exe 运行也改成由 `QProcess` 管理，并在 IDE 内提供输入框和输出区。

### 7.5 `pyproject.toml` 可以后续再同步一下

当前实际文件在：

```text
llm/llm_integration.py
```

如果 `pyproject.toml` 中仍写成根目录的 `llm_integration.py`，后续可以改成真实路径，避免 Qt Creator 项目视图里文件路径不一致。

---

## 8. 建议的后续开发方向

可以继续做的方向：

1. **Review 模式完善**  
   目前数据库已有 `mistake_library`，LLM 里也有 `summarize_error_record()`，可以继续做错因卡片、复习列表和掌握状态。

2. **程序运行托管**  
   把编译成功后的 exe 也交给 `QProcess` 运行，这样可以在 IDE 内输入样例、显示输出，并自动传给 AI 助教。

3. **Problems 双击跳转**  
   当前 Problems 已经显示错误行号，后续可以支持双击跳到对应文件和行。

4. **更完整的文件管理**  
   支持在左侧文件树中新建文件、重命名、删除、刷新。

5. **项目依赖整理**  
   可以补一个 `requirements.txt`，让队友直接：

   ```powershell
   pip install -r requirements.txt
   ```

6. **数据库文件管理**  
   `accoach.db` 是本地数据文件。团队协作时可以考虑不要提交个人本地数据库，或者只提交一个空白初始化数据库。

---

## 9. 简短使用流程

给队友快速上手可以按这个顺序：

```text
1. 安装 Python 依赖和 g++
2. 运行 python main.py
3. 打开项目文件夹
4. 新建或打开一个 .cpp 文件
5. 点击 Question -> Modify，粘贴题目并保存分析
6. 点击 Question -> Check，确认题目已分析完成
7. 点击 API 配置项，输入自己的 DeepSeek API Key
8. 编写代码
9. 点击 Compile & Run 查看编译情况
10. 点击 Analyse / 求助助教
11. 选择自动判断、纠错调试或下一步提示
12. 查看右侧 AI 助教提示，并根据提示修改代码
```

---

## 10. 一句话总结

当前项目的主线是：

```text
C++ 编辑与编译
→ 题目绑定与题面分析
→ 收集代码/运行/OJ 上下文
→ 调用 LLM 判断学生状态
→ 生成分步提示
→ 保存到数据库
→ 在右侧面板展示并高亮代码
```

也就是说，AC Coach 不是单纯聊天窗口，而是把“代码、题目、编译结果、学生补充信息、历史提示”组织起来，给学生一个更贴近编程学习过程的 AI 助教。
