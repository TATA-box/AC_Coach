# AC Coach

Hello!现在我大致按自己的想法写了一个基础的IDE框架，目前还比较简陋，为了实现需求，我设置了两个模式，一个是coding模式用于敲代码，一个是review模式用于用途中的复习那一大板块，然后目前我主要做了coding模式下的一些基础操作，具体如下：

- 打开项目文件夹
- 左侧文件树浏览代码文件
- 双击文件后在编辑器中打开
- 支持多标签页编辑
- 支持保存当前文件 / 保存所有文件
- 支持撤销、重做、剪切、复制、粘贴
- 支持调用 `g++` 编译当前 `.cpp` 文件
- 编译信息输出到底部 Build Log
- 编译错误 / warning 显示到底部 Problems
- 编译成功后弹出 cmd 窗口运行生成的 `.exe`

页面整体的UI设计如下：

![01457da78af91968e33f82b7f65035dc](C:\Users\Tiant\Documents\xwechat_files\wxid_lgvs0rlx862f22_9f2a\temp\RWTemp\2026-05\9e20f478899dc29eb19741386f9343c8\01457da78af91968e33f82b7f65035dc.jpg)

后续还有一点就是代码编辑区我目前是用的QPlainTextEdit类，然后后面可以研究一下QScintilla，应该可以替换以此优化代码体验，然后整体UI布局可能还有点小问题，其次一些细节方面的IDE使用体验还是可以继续优化的，比如快捷建，在文件树创建文件之类等等。如果设计上有什么问题可以随时改。

---

## 项目结构

```text
AC_coach/
├─ main.py                  # 程序入口
├─ mainwindow.py            # 主窗口逻辑，负责连接 UI 和功能模块
├─ pyproject.toml           # PySide6 Project 配置
│
├─ ui/
│  ├─ form.ui               # Qt Creator / Qt Designer 设计的 UI 文件
│  └─ ui_form.py            # 由 form.ui 自动生成的 Python UI 文件
│
└─ app/
   ├─ editor_manager.py     # 管理编辑器标签页、打开文件、保存文件
   ├─ file_manager.py       # 负责文件读写
   ├─ cpp_runner.py         # 调用 g++ 编译并运行 C++ 文件
   ├─ panel_manager.py      # 管理底部面板
   └─ coach_service.py      # AI 助教功能预留
```

---

## 各文件作用

### `main.py`

程序入口文件。

主要作用：

- 创建 `QApplication`
- 创建并显示 `MainWindow`

运行项目时执行：

```powershell
python main.py
```

或者在QT Creator右侧项目栏将运行程序设成main.py运行

---

### `mainwindow.py`

主窗口逻辑文件。

主要作用：

- 加载 `ui_form.py` 里的界面
- 构建文件树
- 初始化 Editor Manager等类
- 连接菜单各功能信号与对应Manager操作
- 处理切换模式，show about，Exit等操作【操作比较简单就没有单独建类，暂时放在main window里】

简单来说，`mainwindow.py` 是整个程序的主控制中心。

---

### `ui/form.ui`

用 Qt Creator / Qt Designer 设计出来的界面文件。

---

### `ui/ui_form.py`

由 `form.ui` 自动生成的 Python 文件。

如果修改了 `form.ui`，需要重新生成 `ui_form.py`。

生成命令：

```powershell
pyside6-uic ui\form.ui -o ui\ui_form.py
```

---

### `app/editor_manager.py`

编辑器管理模块。

主要作用：

- 打开文件
- 创建代码编辑区
- 管理 Tab 页
- 保存当前文件
- 保存所有文件
- 关闭文件时检查是否有未保存修改
- 提供撤销、重做、剪切、复制、粘贴功能

基本所有和“代码编辑器”有关的逻辑都放在这里。

---

### `app/file_manager.py`

文件读写模块。

主要作用：

- 读取文件内容
- 写入文件内容

`EditorManager` 会调用它。

---

### `app/cpp_runner.py`

C++ 编译运行模块。

主要作用：

- 调用 `g++` 编译当前文件
- 生成同名 `.exe`
- 收集编译输出，打印至panel的Compile Log
- 解析 g++ 的 error / warning / note
- 编译成功后弹出 cmd 窗口运行 exe

---

### `app/panel_manager.py`

底部面板管理模块。

主要作用：

- 向 Compile Log 显示编译进程
- 在 Problems 表格中显示编译错误

---

### `app/coach_service.py`

AI 助教功能预留模块。

---

## 环境要求

当前开发环境如下：

```text
Operating System: Windows
Python: 3.14 64-bit
PySide6: 6.11.1
Qt Creator: 19.0.1
```

记得安装 PySide6

