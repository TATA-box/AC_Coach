# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'form.ui'
##
## Created by: Qt User Interface Compiler version 6.11.1
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QAction, QBrush, QColor, QConicalGradient,
    QCursor, QFont, QFontDatabase, QGradient,
    QIcon, QImage, QKeySequence, QLinearGradient,
    QPainter, QPalette, QPixmap, QRadialGradient,
    QTransform)
from PySide6.QtWidgets import (QAbstractItemView, QApplication, QComboBox, QGridLayout,
    QHBoxLayout, QHeaderView, QLabel, QLineEdit,
    QMainWindow, QMenu, QMenuBar, QPushButton,
    QScrollArea, QSizePolicy, QSpacerItem, QSplitter,
    QStackedWidget, QStatusBar, QTabWidget, QTableWidget,
    QTableWidgetItem, QTextEdit, QTreeView, QVBoxLayout,
    QWidget)

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        if not MainWindow.objectName():
            MainWindow.setObjectName(u"MainWindow")
        MainWindow.resize(800, 600)
        self.actionOpen_Folder = QAction(MainWindow)
        self.actionOpen_Folder.setObjectName(u"actionOpen_Folder")
        self.actionSave = QAction(MainWindow)
        self.actionSave.setObjectName(u"actionSave")
        self.actionSave_all = QAction(MainWindow)
        self.actionSave_all.setObjectName(u"actionSave_all")
        self.actionExit = QAction(MainWindow)
        self.actionExit.setObjectName(u"actionExit")
        self.actionSave_2 = QAction(MainWindow)
        self.actionSave_2.setObjectName(u"actionSave_2")
        self.actionSave_All = QAction(MainWindow)
        self.actionSave_All.setObjectName(u"actionSave_All")
        self.actionExit_2 = QAction(MainWindow)
        self.actionExit_2.setObjectName(u"actionExit_2")
        self.actionUndo = QAction(MainWindow)
        self.actionUndo.setObjectName(u"actionUndo")
        self.actionRedo = QAction(MainWindow)
        self.actionRedo.setObjectName(u"actionRedo")
        self.actionCut = QAction(MainWindow)
        self.actionCut.setObjectName(u"actionCut")
        self.actionCopy = QAction(MainWindow)
        self.actionCopy.setObjectName(u"actionCopy")
        self.actionPaste = QAction(MainWindow)
        self.actionPaste.setObjectName(u"actionPaste")
        self.actionFind = QAction(MainWindow)
        self.actionFind.setObjectName(u"actionFind")
        self.act_compile_run = QAction(MainWindow)
        self.act_compile_run.setObjectName(u"act_compile_run")
        self.act_about = QAction(MainWindow)
        self.act_about.setObjectName(u"act_about")
        self.act_openfolder = QAction(MainWindow)
        self.act_openfolder.setObjectName(u"act_openfolder")
        self.act_save = QAction(MainWindow)
        self.act_save.setObjectName(u"act_save")
        self.act_saveall = QAction(MainWindow)
        self.act_saveall.setObjectName(u"act_saveall")
        self.act_exit = QAction(MainWindow)
        self.act_exit.setObjectName(u"act_exit")
        self.act_undo = QAction(MainWindow)
        self.act_undo.setObjectName(u"act_undo")
        self.act_redo = QAction(MainWindow)
        self.act_redo.setObjectName(u"act_redo")
        self.act_copy = QAction(MainWindow)
        self.act_copy.setObjectName(u"act_copy")
        self.act_cut = QAction(MainWindow)
        self.act_cut.setObjectName(u"act_cut")
        self.act_paste = QAction(MainWindow)
        self.act_paste.setObjectName(u"act_paste")
        self.act_find = QAction(MainWindow)
        self.act_find.setObjectName(u"act_find")
        self.act_new = QAction(MainWindow)
        self.act_new.setObjectName(u"act_new")
        self.act_new.setMenuRole(QAction.MenuRole.TextHeuristicRole)
        self.actionCreat_File = QAction(MainWindow)
        self.actionCreat_File.setObjectName(u"actionCreat_File")
        self.actionModify = QAction(MainWindow)
        self.actionModify.setObjectName(u"actionModify")
        self.actionCheck = QAction(MainWindow)
        self.actionCheck.setObjectName(u"actionCheck")
        self.act_analyse = QAction(MainWindow)
        self.act_analyse.setObjectName(u"act_analyse")
        self.act_modify = QAction(MainWindow)
        self.act_modify.setObjectName(u"act_modify")
        self.act_check = QAction(MainWindow)
        self.act_check.setObjectName(u"act_check")
        self.act_config = QAction(MainWindow)
        self.act_config.setObjectName(u"act_config")
        self.centralwidget = QWidget(MainWindow)
        self.centralwidget.setObjectName(u"centralwidget")
        self.gridLayout = QGridLayout(self.centralwidget)
        self.gridLayout.setObjectName(u"gridLayout")
        self.gridLayout.setContentsMargins(0, 0, 0, 0)
        self.modeWidget = QWidget(self.centralwidget)
        self.modeWidget.setObjectName(u"modeWidget")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.modeWidget.sizePolicy().hasHeightForWidth())
        self.modeWidget.setSizePolicy(sizePolicy)
        self.modeWidget.setMinimumSize(QSize(56, 0))
        self.modeWidget.setMaximumSize(QSize(56, 16777215))
        self.verticalLayout = QVBoxLayout(self.modeWidget)
        self.verticalLayout.setSpacing(8)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(0, -1, 0, -1)
        self.codingmodeButton = QPushButton(self.modeWidget)
        self.codingmodeButton.setObjectName(u"codingmodeButton")
        sizePolicy1 = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.codingmodeButton.sizePolicy().hasHeightForWidth())
        self.codingmodeButton.setSizePolicy(sizePolicy1)
        self.codingmodeButton.setMinimumSize(QSize(0, 42))
        self.codingmodeButton.setCheckable(True)
        self.codingmodeButton.setChecked(True)

        self.verticalLayout.addWidget(self.codingmodeButton)

        self.reviewmodeButton = QPushButton(self.modeWidget)
        self.reviewmodeButton.setObjectName(u"reviewmodeButton")
        sizePolicy1.setHeightForWidth(self.reviewmodeButton.sizePolicy().hasHeightForWidth())
        self.reviewmodeButton.setSizePolicy(sizePolicy1)
        self.reviewmodeButton.setMinimumSize(QSize(0, 42))
        self.reviewmodeButton.setCheckable(True)

        self.verticalLayout.addWidget(self.reviewmodeButton)

        self.verticalSpacer = QSpacerItem(20, 458, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout.addItem(self.verticalSpacer)


        self.gridLayout.addWidget(self.modeWidget, 0, 0, 1, 1)

        self.mainstackedWidget = QStackedWidget(self.centralwidget)
        self.mainstackedWidget.setObjectName(u"mainstackedWidget")
        sizePolicy2 = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        sizePolicy2.setHorizontalStretch(0)
        sizePolicy2.setVerticalStretch(0)
        sizePolicy2.setHeightForWidth(self.mainstackedWidget.sizePolicy().hasHeightForWidth())
        self.mainstackedWidget.setSizePolicy(sizePolicy2)
        self.mainstackedWidget.setMinimumSize(QSize(500, 0))
        self.mainstackedWidget.setMaximumSize(QSize(16777215, 16777215))
        self.codingPage = QWidget()
        self.codingPage.setObjectName(u"codingPage")
        self.horizontalLayout = QHBoxLayout(self.codingPage)
        self.horizontalLayout.setSpacing(0)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalLayout.setContentsMargins(0, 0, 0, 0)
        self.codingMainSplitter = QSplitter(self.codingPage)
        self.codingMainSplitter.setObjectName(u"codingMainSplitter")
        sizePolicy2.setHeightForWidth(self.codingMainSplitter.sizePolicy().hasHeightForWidth())
        self.codingMainSplitter.setSizePolicy(sizePolicy2)
        self.codingMainSplitter.setMaximumSize(QSize(16777215, 16777215))
        self.codingMainSplitter.setOrientation(Qt.Orientation.Horizontal)
        self.projectTree = QTreeView(self.codingMainSplitter)
        self.projectTree.setObjectName(u"projectTree")
        sizePolicy2.setHeightForWidth(self.projectTree.sizePolicy().hasHeightForWidth())
        self.projectTree.setSizePolicy(sizePolicy2)
        self.projectTree.setMinimumSize(QSize(0, 0))
        self.projectTree.setMaximumSize(QSize(150, 16777215))
        self.projectTree.setAlternatingRowColors(True)
        self.projectTree.setAnimated(True)
        self.projectTree.setHeaderHidden(True)
        self.codingMainSplitter.addWidget(self.projectTree)
        self.centerWidget = QWidget(self.codingMainSplitter)
        self.centerWidget.setObjectName(u"centerWidget")
        sizePolicy2.setHeightForWidth(self.centerWidget.sizePolicy().hasHeightForWidth())
        self.centerWidget.setSizePolicy(sizePolicy2)
        self.centerWidget.setMinimumSize(QSize(0, 0))
        self.centerWidget.setMaximumSize(QSize(16777215, 16777215))
        self.verticalLayout_2 = QVBoxLayout(self.centerWidget)
        self.verticalLayout_2.setSpacing(0)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.verticalLayout_2.setContentsMargins(0, 0, 0, 0)
        self.splitter_2 = QSplitter(self.centerWidget)
        self.splitter_2.setObjectName(u"splitter_2")
        sizePolicy2.setHeightForWidth(self.splitter_2.sizePolicy().hasHeightForWidth())
        self.splitter_2.setSizePolicy(sizePolicy2)
        self.splitter_2.setOrientation(Qt.Orientation.Vertical)
        self.editorWidget = QTabWidget(self.splitter_2)
        self.editorWidget.setObjectName(u"editorWidget")
        self.editorWidget.setMinimumSize(QSize(400, 0))
        self.editorWidget.setMaximumSize(QSize(16777215, 16777215))
        self.editorWidget.setTabShape(QTabWidget.TabShape.Rounded)
        self.editorWidget.setDocumentMode(True)
        self.editorWidget.setTabsClosable(True)
        self.editorWidget.setMovable(True)
        self.welcomePage = QWidget()
        self.welcomePage.setObjectName(u"welcomePage")
        self.editorWidget.addTab(self.welcomePage, "")
        self.tab_4 = QWidget()
        self.tab_4.setObjectName(u"tab_4")
        self.editorWidget.addTab(self.tab_4, "")
        self.splitter_2.addWidget(self.editorWidget)
        self.panelWidget = QTabWidget(self.splitter_2)
        self.panelWidget.setObjectName(u"panelWidget")
        sizePolicy1.setHeightForWidth(self.panelWidget.sizePolicy().hasHeightForWidth())
        self.panelWidget.setSizePolicy(sizePolicy1)
        self.panelWidget.setMinimumSize(QSize(0, 200))
        self.panelWidget.setDocumentMode(True)
        self.problemsPage = QWidget()
        self.problemsPage.setObjectName(u"problemsPage")
        self.horizontalLayout_3 = QHBoxLayout(self.problemsPage)
        self.horizontalLayout_3.setSpacing(0)
        self.horizontalLayout_3.setObjectName(u"horizontalLayout_3")
        self.horizontalLayout_3.setContentsMargins(0, 0, 0, 0)
        self.problemWidget = QTableWidget(self.problemsPage)
        if (self.problemWidget.columnCount() < 5):
            self.problemWidget.setColumnCount(5)
        __qtablewidgetitem = QTableWidgetItem()
        self.problemWidget.setHorizontalHeaderItem(0, __qtablewidgetitem)
        __qtablewidgetitem1 = QTableWidgetItem()
        self.problemWidget.setHorizontalHeaderItem(1, __qtablewidgetitem1)
        __qtablewidgetitem2 = QTableWidgetItem()
        self.problemWidget.setHorizontalHeaderItem(2, __qtablewidgetitem2)
        __qtablewidgetitem3 = QTableWidgetItem()
        self.problemWidget.setHorizontalHeaderItem(3, __qtablewidgetitem3)
        __qtablewidgetitem4 = QTableWidgetItem()
        self.problemWidget.setHorizontalHeaderItem(4, __qtablewidgetitem4)
        self.problemWidget.setObjectName(u"problemWidget")
        self.problemWidget.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.problemWidget.setAlternatingRowColors(True)
        self.problemWidget.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.problemWidget.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.problemWidget.setShowGrid(False)
        self.problemWidget.setWordWrap(True)
        self.problemWidget.setColumnCount(5)
        self.problemWidget.verticalHeader().setVisible(False)

        self.horizontalLayout_3.addWidget(self.problemWidget)

        self.panelWidget.addTab(self.problemsPage, "")
        self.compilelogPage = QWidget()
        self.compilelogPage.setObjectName(u"compilelogPage")
        self.horizontalLayout_2 = QHBoxLayout(self.compilelogPage)
        self.horizontalLayout_2.setSpacing(0)
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.horizontalLayout_2.setContentsMargins(0, 0, 0, 0)
        self.compilelogEdit = QTextEdit(self.compilelogPage)
        self.compilelogEdit.setObjectName(u"compilelogEdit")
        sizePolicy2.setHeightForWidth(self.compilelogEdit.sizePolicy().hasHeightForWidth())
        self.compilelogEdit.setSizePolicy(sizePolicy2)
        self.compilelogEdit.setReadOnly(True)

        self.horizontalLayout_2.addWidget(self.compilelogEdit)

        self.panelWidget.addTab(self.compilelogPage, "")
        self.splitter_2.addWidget(self.panelWidget)

        self.verticalLayout_2.addWidget(self.splitter_2)

        self.codingMainSplitter.addWidget(self.centerWidget)
        self.aiwidget = QWidget(self.codingMainSplitter)
        self.aiwidget.setObjectName(u"aiwidget")
        self.verticalLayout_3 = QVBoxLayout(self.aiwidget)
        self.verticalLayout_3.setSpacing(0)
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.verticalLayout_3.setContentsMargins(0, 0, 0, 0)
        self.coachStack = QStackedWidget(self.aiwidget)
        self.coachStack.setObjectName(u"coachStack")
        sizePolicy2.setHeightForWidth(self.coachStack.sizePolicy().hasHeightForWidth())
        self.coachStack.setSizePolicy(sizePolicy2)
        self.coachConfigPage = QWidget()
        self.coachConfigPage.setObjectName(u"coachConfigPage")
        self.coachStack.addWidget(self.coachConfigPage)
        self.coachResultPage = QWidget()
        self.coachResultPage.setObjectName(u"coachResultPage")
        self.coachStack.addWidget(self.coachResultPage)

        self.verticalLayout_3.addWidget(self.coachStack)

        self.codingMainSplitter.addWidget(self.aiwidget)

        self.horizontalLayout.addWidget(self.codingMainSplitter)

        self.mainstackedWidget.addWidget(self.codingPage)
        self.reviewPage = QWidget()
        self.reviewPage.setObjectName(u"reviewPage")
        self.verticalLayout_7 = QVBoxLayout(self.reviewPage)
        self.verticalLayout_7.setObjectName(u"verticalLayout_7")
        self.titlePage = QHBoxLayout()
        self.titlePage.setObjectName(u"titlePage")
        self.titleLabel = QLabel(self.reviewPage)
        self.titleLabel.setObjectName(u"titleLabel")
        self.titleLabel.setStyleSheet(u"font-size: 16px;\n"
"font-weight: bold;\n"
"color: #2c3e50;")

        self.titlePage.addWidget(self.titleLabel)

        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.titlePage.addItem(self.horizontalSpacer)

        self.refreshButton = QPushButton(self.reviewPage)
        self.refreshButton.setObjectName(u"refreshButton")
        self.refreshButton.setStyleSheet(u"background-color: #3498db;\n"
"color: white;\n"
"border: none;\n"
"border-radius: 4px;\n"
"padding: 6px 12px;")

        self.titlePage.addWidget(self.refreshButton)

        self.generatereviewButton = QPushButton(self.reviewPage)
        self.generatereviewButton.setObjectName(u"generatereviewButton")
        self.generatereviewButton.setStyleSheet(u"background-color: #3498db;\n"
"color: white;\n"
"border: none;\n"
"border-radius: 4px;\n"
"padding: 6px 12px;")

        self.titlePage.addWidget(self.generatereviewButton)


        self.verticalLayout_7.addLayout(self.titlePage)

        self.filterPage = QHBoxLayout()
        self.filterPage.setObjectName(u"filterPage")
        self.filterLabel = QLabel(self.reviewPage)
        self.filterLabel.setObjectName(u"filterLabel")

        self.filterPage.addWidget(self.filterLabel)

        self.filterCombo = QComboBox(self.reviewPage)
        self.filterCombo.addItem("")
        self.filterCombo.addItem("")
        self.filterCombo.addItem("")
        self.filterCombo.setObjectName(u"filterCombo")
        self.filterCombo.setStyleSheet(u"QComboBox {\n"
"    border: 1px solid #ddd;\n"
"    border-radius: 4px;\n"
"    padding: 4px 8px;\n"
"    min-width: 100px;\n"
"}")

        self.filterPage.addWidget(self.filterCombo)

        self.knowledgeLabel = QLabel(self.reviewPage)
        self.knowledgeLabel.setObjectName(u"knowledgeLabel")

        self.filterPage.addWidget(self.knowledgeLabel)

        self.knowledgeCombo = QComboBox(self.reviewPage)
        self.knowledgeCombo.setObjectName(u"knowledgeCombo")
        self.knowledgeCombo.setStyleSheet(u"QComboBox {\n"
"    border: 1px solid #ddd;\n"
"    border-radius: 4px;\n"
"    padding: 4px 8px;\n"
"    min-width: 100px;\n"
"}")

        self.filterPage.addWidget(self.knowledgeCombo)

        self.errorLabel = QLabel(self.reviewPage)
        self.errorLabel.setObjectName(u"errorLabel")

        self.filterPage.addWidget(self.errorLabel)

        self.searchEdit = QLineEdit(self.reviewPage)
        self.searchEdit.setObjectName(u"searchEdit")
        self.searchEdit.setStyleSheet(u"QLineEdit {\n"
"    border: 1px solid #ddd;\n"
"    border-radius: 4px;\n"
"    padding: 4px 8px;\n"
"    min-width: 150px;\n"
"}")

        self.filterPage.addWidget(self.searchEdit)

        self.horizontalSpacer_2 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.filterPage.addItem(self.horizontalSpacer_2)

        self.showexamsButton = QPushButton(self.reviewPage)
        self.showexamsButton.setObjectName(u"showexamsButton")
        self.showexamsButton.setStyleSheet(u"background-color: #3498db;\n"
"color: white;\n"
"border: none;\n"
"border-radius: 4px;\n"
"padding: 6px 12px;")

        self.filterPage.addWidget(self.showexamsButton)


        self.verticalLayout_7.addLayout(self.filterPage)

        self.scrollArea = QScrollArea(self.reviewPage)
        self.scrollArea.setObjectName(u"scrollArea")
        self.scrollArea.setStyleSheet(u"QScrollArea {\n"
"    border: none;\n"
"    background-color: transparent;\n"
"}")
        self.scrollArea.setWidgetResizable(True)
        self.scrollContent = QWidget()
        self.scrollContent.setObjectName(u"scrollContent")
        self.scrollContent.setGeometry(QRect(0, 0, 720, 446))
        self.verticalLayout_8 = QVBoxLayout(self.scrollContent)
        self.verticalLayout_8.setObjectName(u"verticalLayout_8")
        self.scrollArea.setWidget(self.scrollContent)

        self.verticalLayout_7.addWidget(self.scrollArea)

        self.statsLabel = QLabel(self.reviewPage)
        self.statsLabel.setObjectName(u"statsLabel")
        self.statsLabel.setStyleSheet(u"color: rgb(136, 136, 136);")

        self.verticalLayout_7.addWidget(self.statsLabel)

        self.mainstackedWidget.addWidget(self.reviewPage)

        self.gridLayout.addWidget(self.mainstackedWidget, 0, 1, 1, 1)

        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QMenuBar(MainWindow)
        self.menubar.setObjectName(u"menubar")
        self.menubar.setGeometry(QRect(0, 0, 800, 22))
        self.menuFile = QMenu(self.menubar)
        self.menuFile.setObjectName(u"menuFile")
        self.menuEditor = QMenu(self.menubar)
        self.menuEditor.setObjectName(u"menuEditor")
        self.menuRun = QMenu(self.menubar)
        self.menuRun.setObjectName(u"menuRun")
        self.menuHelp = QMenu(self.menubar)
        self.menuHelp.setObjectName(u"menuHelp")
        self.menuCoach = QMenu(self.menubar)
        self.menuCoach.setObjectName(u"menuCoach")
        self.menuQuestion = QMenu(self.menubar)
        self.menuQuestion.setObjectName(u"menuQuestion")
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QStatusBar(MainWindow)
        self.statusbar.setObjectName(u"statusbar")
        MainWindow.setStatusBar(self.statusbar)

        self.menubar.addAction(self.menuFile.menuAction())
        self.menubar.addAction(self.menuEditor.menuAction())
        self.menubar.addAction(self.menuRun.menuAction())
        self.menubar.addAction(self.menuQuestion.menuAction())
        self.menubar.addAction(self.menuCoach.menuAction())
        self.menubar.addAction(self.menuHelp.menuAction())
        self.menuFile.addAction(self.act_new)
        self.menuFile.addAction(self.act_openfolder)
        self.menuFile.addSeparator()
        self.menuFile.addAction(self.act_save)
        self.menuFile.addAction(self.act_saveall)
        self.menuFile.addSeparator()
        self.menuFile.addAction(self.act_exit)
        self.menuEditor.addAction(self.act_undo)
        self.menuEditor.addAction(self.act_redo)
        self.menuEditor.addSeparator()
        self.menuEditor.addAction(self.act_copy)
        self.menuEditor.addAction(self.act_cut)
        self.menuEditor.addAction(self.act_paste)
        self.menuEditor.addSeparator()
        self.menuEditor.addAction(self.act_find)
        self.menuRun.addAction(self.act_compile_run)
        self.menuHelp.addAction(self.act_about)
        self.menuCoach.addAction(self.act_config)
        self.menuCoach.addAction(self.act_analyse)
        self.menuQuestion.addAction(self.act_modify)
        self.menuQuestion.addAction(self.act_check)

        self.retranslateUi(MainWindow)

        self.mainstackedWidget.setCurrentIndex(1)
        self.editorWidget.setCurrentIndex(0)
        self.panelWidget.setCurrentIndex(0)


        QMetaObject.connectSlotsByName(MainWindow)
    # setupUi

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QCoreApplication.translate("MainWindow", u"AC_Coach", None))
        self.actionOpen_Folder.setText(QCoreApplication.translate("MainWindow", u"Open Folder", None))
        self.actionSave.setText(QCoreApplication.translate("MainWindow", u"Save", None))
        self.actionSave_all.setText(QCoreApplication.translate("MainWindow", u"Save all", None))
        self.actionExit.setText(QCoreApplication.translate("MainWindow", u"Exit", None))
        self.actionSave_2.setText(QCoreApplication.translate("MainWindow", u"Save", None))
        self.actionSave_All.setText(QCoreApplication.translate("MainWindow", u"Save All", None))
        self.actionExit_2.setText(QCoreApplication.translate("MainWindow", u"Exit", None))
        self.actionUndo.setText(QCoreApplication.translate("MainWindow", u"Undo", None))
        self.actionRedo.setText(QCoreApplication.translate("MainWindow", u"Redo", None))
        self.actionCut.setText(QCoreApplication.translate("MainWindow", u"Cut", None))
        self.actionCopy.setText(QCoreApplication.translate("MainWindow", u"Copy", None))
        self.actionPaste.setText(QCoreApplication.translate("MainWindow", u"Paste", None))
        self.actionFind.setText(QCoreApplication.translate("MainWindow", u"Find", None))
        self.act_compile_run.setText(QCoreApplication.translate("MainWindow", u"Compile and Run", None))
        self.act_about.setText(QCoreApplication.translate("MainWindow", u"About", None))
        self.act_openfolder.setText(QCoreApplication.translate("MainWindow", u"Open Folder", None))
        self.act_save.setText(QCoreApplication.translate("MainWindow", u"Save", None))
        self.act_saveall.setText(QCoreApplication.translate("MainWindow", u"Save All", None))
        self.act_exit.setText(QCoreApplication.translate("MainWindow", u"Exit", None))
        self.act_undo.setText(QCoreApplication.translate("MainWindow", u"Undo", None))
        self.act_redo.setText(QCoreApplication.translate("MainWindow", u"Redo", None))
        self.act_copy.setText(QCoreApplication.translate("MainWindow", u"Copy", None))
        self.act_cut.setText(QCoreApplication.translate("MainWindow", u"Cut", None))
        self.act_paste.setText(QCoreApplication.translate("MainWindow", u"Paste", None))
        self.act_find.setText(QCoreApplication.translate("MainWindow", u"Find", None))
        self.act_new.setText(QCoreApplication.translate("MainWindow", u"New", None))
        self.actionCreat_File.setText(QCoreApplication.translate("MainWindow", u"Creat File", None))
        self.actionModify.setText(QCoreApplication.translate("MainWindow", u"Modify", None))
        self.actionCheck.setText(QCoreApplication.translate("MainWindow", u"Check", None))
        self.act_analyse.setText(QCoreApplication.translate("MainWindow", u"analyse", None))
        self.act_modify.setText(QCoreApplication.translate("MainWindow", u"Modify", None))
        self.act_check.setText(QCoreApplication.translate("MainWindow", u"Check", None))
        self.act_config.setText(QCoreApplication.translate("MainWindow", u"config", None))
        self.codingmodeButton.setText(QCoreApplication.translate("MainWindow", u"Coding", None))
        self.reviewmodeButton.setText(QCoreApplication.translate("MainWindow", u"Review", None))
        self.editorWidget.setTabText(self.editorWidget.indexOf(self.welcomePage), QCoreApplication.translate("MainWindow", u"Welcome", None))
        self.editorWidget.setTabText(self.editorWidget.indexOf(self.tab_4), QCoreApplication.translate("MainWindow", u"Tab 2", None))
        ___qtablewidgetitem = self.problemWidget.horizontalHeaderItem(0)
        ___qtablewidgetitem.setText(QCoreApplication.translate("MainWindow", u"level", None))
        ___qtablewidgetitem1 = self.problemWidget.horizontalHeaderItem(1)
        ___qtablewidgetitem1.setText(QCoreApplication.translate("MainWindow", u"File", None))
        ___qtablewidgetitem2 = self.problemWidget.horizontalHeaderItem(2)
        ___qtablewidgetitem2.setText(QCoreApplication.translate("MainWindow", u"Line", None))
        ___qtablewidgetitem3 = self.problemWidget.horizontalHeaderItem(3)
        ___qtablewidgetitem3.setText(QCoreApplication.translate("MainWindow", u"Column", None))
        ___qtablewidgetitem4 = self.problemWidget.horizontalHeaderItem(4)
        ___qtablewidgetitem4.setText(QCoreApplication.translate("MainWindow", u"Message", None))
        self.panelWidget.setTabText(self.panelWidget.indexOf(self.problemsPage), QCoreApplication.translate("MainWindow", u"Problems", None))
        self.panelWidget.setTabText(self.panelWidget.indexOf(self.compilelogPage), QCoreApplication.translate("MainWindow", u"Build Log", None))
        self.titleLabel.setText(QCoreApplication.translate("MainWindow", u"\u9519\u56e0\u5e93", None))
        self.refreshButton.setText(QCoreApplication.translate("MainWindow", u"\u5237\u65b0", None))
        self.generatereviewButton.setText(QCoreApplication.translate("MainWindow", u"\u751f\u6210\u590d\u4e60\u8d44\u6599", None))
        self.filterLabel.setText(QCoreApplication.translate("MainWindow", u"\u663e\u793a\uff1a", None))
        self.filterCombo.setItemText(0, QCoreApplication.translate("MainWindow", u"\u5168\u90e8", None))
        self.filterCombo.setItemText(1, QCoreApplication.translate("MainWindow", u"\u672a\u638c\u63e1", None))
        self.filterCombo.setItemText(2, QCoreApplication.translate("MainWindow", u"\u5df2\u638c\u63e1", None))

        self.knowledgeLabel.setText(QCoreApplication.translate("MainWindow", u"\u77e5\u8bc6\u70b9\uff1a", None))
        self.errorLabel.setText(QCoreApplication.translate("MainWindow", u"\u9519\u8bef\uff1a", None))
        self.showexamsButton.setText(QCoreApplication.translate("MainWindow", u"\u67e5\u770b\u5df2\u751f\u6210\u7684\u8003\u9898", None))
        self.statsLabel.setText(QCoreApplication.translate("MainWindow", u"\u51710\u6761\u9519\u56e0", None))
        self.menuFile.setTitle(QCoreApplication.translate("MainWindow", u"File", None))
        self.menuEditor.setTitle(QCoreApplication.translate("MainWindow", u"Edit", None))
        self.menuRun.setTitle(QCoreApplication.translate("MainWindow", u"Run", None))
        self.menuHelp.setTitle(QCoreApplication.translate("MainWindow", u"Help", None))
        self.menuCoach.setTitle(QCoreApplication.translate("MainWindow", u"Coach", None))
        self.menuQuestion.setTitle(QCoreApplication.translate("MainWindow", u"Question", None))
    # retranslateUi

