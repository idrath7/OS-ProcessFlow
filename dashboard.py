"""Premium desktop UI: editable process input + live CPU/RAM simulation."""

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QColor, QFont, QPainter
from PySide6.QtWidgets import (
    QWidget,
    QMainWindow,
    QFrame,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QLabel,
    QPushButton,
    QLineEdit,
    QSpinBox,
    QComboBox,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QMessageBox,
    QAbstractItemView,
    QScrollArea,
    QProgressBar,
    QSizePolicy,
    QApplication,
)
from scheduler import simulate, make_segments
from styles import LIGHT, DARK, get_style

COLORS = [
    "#365FD9",
    "#8759CC",
    "#14899C",
    "#14916E",
    "#D38A26",
    "#D45789",
    "#5F6CCC",
    "#D26B40",
]


def panel(title, subtitle=None):
    frame = QFrame()
    frame.setObjectName("panel")
    layout = QVBoxLayout(frame)
    layout.setContentsMargins(22, 20, 22, 20)
    layout.setSpacing(14)
    heading = QLabel(title)
    heading.setObjectName("sectionTitle")
    layout.addWidget(heading)
    if subtitle:
        caption = QLabel(subtitle)
        caption.setObjectName("muted")
        caption.setWordWrap(True)
        layout.addWidget(caption)
    return frame, layout


def field(text, widget):
    box = QWidget()
    layout = QVBoxLayout(box)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(5)
    label = QLabel(text)
    label.setObjectName("muted")
    layout.addWidget(label)
    layout.addWidget(widget)
    return box


class GanttWidget(QWidget):
    """Custom Qt painted timeline; gray denotes future, color denotes elapsed ticks."""

    def __init__(self):
        super().__init__()
        self.events = []
        self.progress = 0
        self.color_by_pid = {}
        self.theme = "light"
        self.setMinimumHeight(137)
        self.setMinimumWidth(550)

    def update_data(self, events, progress, colors):
        self.events = events
        self.progress = progress
        self.color_by_pid = colors
        segments = make_segments(events)
        self.setMinimumWidth(
            max(550, 30 + sum(max(58, (s["end"] - s["start"]) * 34) for s in segments))
        )
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        palette = LIGHT if self.theme == "light" else DARK
        painter.fillRect(self.rect(), QColor(palette["surface"]))
        if not self.events:
            painter.setPen(QColor(palette["muted"]))
            painter.drawText(
                self.rect(),
                Qt.AlignCenter,
                "Run scheduling to generate the Gantt chart",
            )
            return
        blocks = make_segments(self.events)
        x = 12
        for block in blocks:
            pid = block["pid"]
            start, end = block["start"], block["end"]
            width = max(58, (end - start) * 34)
            progressed = min(max(self.progress - start, 0), end - start)
            color = QColor(self.color_by_pid.get(pid, "#64748B"))
            painter.setPen(Qt.NoPen)
            painter.setBrush(QColor(palette["future"]))
            painter.drawRoundedRect(x, 24, width - 4, 55, 7, 7)
            if progressed:
                fill_width = (width - 4) * progressed / (end - start)
                painter.setBrush(color)
                painter.drawRoundedRect(x, 24, int(fill_width), 55, 6, 6)
            painter.setPen(QColor("#FFFFFF" if progressed else palette["body"]))
            painter.setFont(QFont("Segoe UI", 12, QFont.Bold))
            painter.drawText(x, 25, width - 4, 53, Qt.AlignCenter, pid)
            painter.setPen(QColor(palette["muted"]))
            painter.setFont(QFont("Segoe UI", 10))
            painter.drawText(x, 86, 55, 20, Qt.AlignLeft, str(start))
            if block == blocks[-1]:
                painter.drawText(x + width - 48, 86, 44, 20, Qt.AlignRight, str(end))
            x += width
        painter.end()


class Dashboard(QWidget):
    def __init__(self):
        super().__init__()
        self.processes = []
        self.events = []
        self.results = []
        self.step = 0
        self.pid_colors = {}
        self.theme = "light"
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.next_step)
        self.build_ui()
        self.load_demo()

    def stat_card(self, caption, value):
        frame = QFrame()
        frame.setObjectName("statusCard")
        frame.setFixedHeight(120)
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(17, 17, 12, 12)
        a = QLabel(caption)
        a.setObjectName("cardTitle")
        b = QLabel(value)
        b.setObjectName("cardValue")
        b.setWordWrap(True)
        layout.addWidget(a)
        layout.addWidget(b)
        layout.addStretch()
        return frame, b

    def make_table(self, labels, height=185):
        table = QTableWidget(0, len(labels))
        table.setHorizontalHeaderLabels(labels)
        table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        table.verticalHeader().setVisible(False)
        table.setAlternatingRowColors(True)
        table.setSelectionBehavior(QAbstractItemView.SelectRows)
        table.setSelectionMode(QAbstractItemView.SingleSelection)
        table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        table.verticalHeader().setDefaultSectionSize(42)
        table.setMinimumHeight(height)
        table.setMaximumHeight(height + 25)
        return table

    def build_ui(self):
        outer = QHBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)
        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(232)
        nav = QVBoxLayout(sidebar)
        nav.setContentsMargins(18, 30, 18, 22)
        nav.setSpacing(12)
        logo = QLabel("◆  PROCESSFLOW")
        logo.setObjectName("logo")
        nav.addWidget(logo)
        brand_desc = QLabel("SCHEDULING & MEMORY LAB")
        brand_desc.setObjectName("brandSubtitle")
        nav.addWidget(brand_desc)
        nav.addSpacing(28)
        self.menu_buttons = []
        for index, title in enumerate(
            ["Dashboard", "CPU Scheduler", "Memory Monitor", "Results"]
        ):
            button = QPushButton(title)
            button.setObjectName("activeMenu" if index == 0 else "menuButton")
            button.setCursor(Qt.PointingHandCursor)
            button.clicked.connect(lambda checked=False, i=index: self.navigate(i))
            nav.addWidget(button)
            self.menu_buttons.append(button)
        nav.addStretch()
        self.theme_btn = QPushButton("Switch to Dark Theme")
        self.theme_btn.setObjectName("themeButton")
        self.theme_btn.setCursor(Qt.PointingHandCursor)
        self.theme_btn.clicked.connect(self.toggle_theme)
        nav.addWidget(self.theme_btn)
        nav.addSpacing(10)
        ver = QLabel("OS PROCESSFLOW  •  v2.0")
        ver.setObjectName("versionText")
        nav.addWidget(ver)
        outer.addWidget(sidebar)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        body = QWidget()
        body.setObjectName("mainBody")
        self.body_layout = QVBoxLayout(body)
        self.body_layout.setContentsMargins(32, 30, 32, 38)
        self.body_layout.setSpacing(20)
        title = QLabel("System Overview")
        title.setObjectName("pageTitle")
        sub = QLabel(
            "Configure processes, simulate execution, and monitor memory in real time"
        )
        sub.setObjectName("pageSubtitle")
        self.body_layout.addWidget(title)
        self.body_layout.addWidget(sub)
        stats = QGridLayout()
        stats.setSpacing(12)
        cards = [
            self.stat_card("TOTAL PROCESSES", "00"),
            self.stat_card("CPU STATE", "IDLE"),
            self.stat_card("MEMORY USAGE", "0 / 512 MB"),
            self.stat_card("SCHEDULER", "ROUND ROBIN"),
        ]
        self.process_count, self.cpu_status, self.ram_status, self.algorithm_status = [
            x[1] for x in cards
        ]
        for i, (card, _) in enumerate(cards):
            stats.addWidget(card, 0, i)
            stats.setColumnStretch(i, 1)
        self.body_layout.addLayout(stats)

        # Process editor
        self.editor_panel, edit = panel(
            "Create a Process",
            "Enter process details below. Each process is added to the ready-to-simulate queue.",
        )
        inputs = QGridLayout()
        inputs.setSpacing(12)
        self.pid_input = QLineEdit()
        self.pid_input.setPlaceholderText("P5")
        self.pid_input.setMaxLength(20)
        self.arrival_input = QSpinBox()
        self.arrival_input.setRange(0, 12000)
        self.arrival_input.setSuffix(" ms")
        self.burst_input = QSpinBox()
        self.burst_input.setRange(1, 3000)
        self.burst_input.setValue(5)
        self.burst_input.setSuffix(" ms")
        self.priority_input = QSpinBox()
        self.priority_input.setRange(1, 1000)
        self.memory_input = QSpinBox()
        self.memory_input.setRange(1, 100000)
        self.memory_input.setValue(100)
        self.memory_input.setSuffix(" MB")
        widgets = [
            ("Process ID", self.pid_input),
            ("Arrival Time", self.arrival_input),
            ("Burst Time", self.burst_input),
            ("Priority", self.priority_input),
            ("Memory Required", self.memory_input),
        ]
        for i, (label, widget) in enumerate(widgets):
            inputs.addWidget(field(label, widget), i // 3, i % 3)
        for col in range(3):
            inputs.setColumnStretch(col, 1)
        edit.addLayout(inputs)
        actions = QHBoxLayout()
        add = QPushButton("+ Add Process")
        add.setObjectName("primaryButton")
        add.clicked.connect(self.add_process)
        clear = QPushButton("Clear Inputs")
        clear.setObjectName("secondaryButton")
        clear.clicked.connect(self.clear_inputs)
        actions.addWidget(add)
        actions.addWidget(clear)
        actions.addStretch()
        edit.addLayout(actions)
        self.body_layout.addWidget(self.editor_panel)

        self.queue_panel, queue_layout = panel("Process Queue")
        qrow = QHBoxLayout()
        qrow.addStretch()
        remove = QPushButton("Delete Selected")
        remove.setObjectName("dangerButton")
        remove.clicked.connect(self.delete_selected)
        qrow.addWidget(remove)
        queue_layout.addLayout(qrow)
        self.process_table = self.make_table(
            ["Process", "Arrival (ms)", "Burst (ms)", "Priority", "Memory (MB)"], 185
        )
        queue_layout.addWidget(self.process_table)
        self.body_layout.addWidget(self.queue_panel)

        # Scheduler controls + painted Gantt
        self.scheduler_panel, sched = panel(
            "CPU Scheduling",
            "Select an algorithm, then play the execution timeline or inspect each time step.",
        )
        cfg = QHBoxLayout()
        self.algorithm_input = QComboBox()
        self.algorithm_input.addItems(["Round Robin", "Priority Scheduling"])
        self.quantum_input = QSpinBox()
        self.quantum_input.setRange(1, 1000)
        self.quantum_input.setValue(2)
        self.quantum_input.setSuffix(" ms")
        self.total_ram_input = QSpinBox()
        self.total_ram_input.setRange(1, 1000000)
        self.total_ram_input.setValue(512)
        self.total_ram_input.setSuffix(" MB")
        self.speed_input = QSpinBox()
        self.speed_input.setRange(80, 2000)
        self.speed_input.setValue(350)
        self.speed_input.setSingleStep(50)
        self.speed_input.setSuffix(" ms/step")
        cfg.addWidget(field("Algorithm", self.algorithm_input), 3)
        cfg.addWidget(field("Quantum", self.quantum_input), 1)
        cfg.addWidget(field("Total RAM", self.total_ram_input), 1)
        cfg.addWidget(field("Animation Speed", self.speed_input), 1)
        sched.addLayout(cfg)
        self.algorithm_input.currentTextChanged.connect(self.on_algorithm_change)
        self.total_ram_input.valueChanged.connect(lambda _value: self.clear_output())
        controls = QHBoxLayout()
        self.run_btn = QPushButton("Generate & Play")
        self.run_btn.setObjectName("primaryButton")
        self.pause_btn = QPushButton("Pause")
        self.pause_btn.setObjectName("secondaryButton")
        self.next_btn = QPushButton("Next Step")
        self.next_btn.setObjectName("secondaryButton")
        self.reset_btn = QPushButton("Reset")
        self.reset_btn.setObjectName("secondaryButton")
        self.run_btn.clicked.connect(self.start_simulation)
        self.pause_btn.clicked.connect(self.toggle_pause)
        self.next_btn.clicked.connect(self.next_step)
        self.reset_btn.clicked.connect(self.reset_simulation)
        for btn in [self.run_btn, self.pause_btn, self.next_btn, self.reset_btn]:
            btn.setCursor(Qt.PointingHandCursor)
            controls.addWidget(btn)
        controls.addStretch()
        sched.addLayout(controls)
        self.execution_label = QLabel("CPU: IDLE  |  Time: 0 ms")
        self.execution_label.setObjectName("sectionTitle")
        sched.addWidget(self.execution_label)
        self.gantt_scroll = QScrollArea()
        self.gantt_scroll.setWidgetResizable(False)
        self.gantt_scroll.setFixedHeight(176)
        self.gantt = GanttWidget()
        self.gantt_scroll.setWidget(self.gantt)
        sched.addWidget(self.gantt_scroll)
        self.step_label = QLabel("Ready to simulate")
        self.step_label.setObjectName("muted")
        sched.addWidget(self.step_label)
        self.body_layout.addWidget(self.scheduler_panel)

        # RAM monitor and per-process state
        self.memory_panel, mem = panel(
            "Live Memory Monitor",
            "Allocated RAM remains in use while a process is ready or running and is released on completion.",
        )
        self.memory_label = QLabel("0 MB used / 512 MB total")
        self.memory_label.setObjectName("sectionTitle")
        mem.addWidget(self.memory_label)
        self.memory_bar = QProgressBar()
        self.memory_bar.setRange(0, 100)
        self.memory_bar.setValue(0)
        mem.addWidget(self.memory_bar)
        self.ram_detail_label = QLabel("No processes loaded in this simulation yet")
        self.ram_detail_label.setWordWrap(True)
        self.ram_detail_label.setObjectName("muted")
        mem.addWidget(self.ram_detail_label)
        state_title = QLabel("Process States")
        state_title.setObjectName("sectionTitle")
        mem.addWidget(state_title)
        self.state_table = self.make_table(
            ["Process", "Execution State", "Remaining (ms)", "RAM (MB)"], 205
        )
        mem.addWidget(self.state_table)
        self.body_layout.addWidget(self.memory_panel)

        # Results
        self.results_panel, result_layout = panel(
            "Scheduling Results",
            "CT = completion time  •  TAT = turnaround time  •  WT = waiting time (including RAM wait).",
        )
        self.result_table = self.make_table(
            ["Process", "Completion (ms)", "Turnaround (ms)", "Waiting (ms)"], 205
        )
        result_layout.addWidget(self.result_table)
        self.average_label = QLabel("Average WT: --   |   Average TAT: --")
        self.average_label.setObjectName("sectionTitle")
        result_layout.addWidget(self.average_label)
        self.body_layout.addWidget(self.results_panel)
        self.body_layout.addStretch()
        self.scroll.setWidget(body)
        outer.addWidget(self.scroll, 1)
        self.on_algorithm_change(self.algorithm_input.currentText())
        self.update_controls()

    def toggle_theme(self):
        self.theme = "dark" if self.theme == "light" else "light"
        self.theme_btn.setText(
            "Switch to Light Theme" if self.theme == "dark" else "Switch to Dark Theme"
        )
        app = QApplication.instance()
        app.setStyleSheet(get_style(self.theme))
        self.gantt.theme = self.theme
        self.gantt.update()
        self.show_states(
            self.events[self.step - 1] if self.step and self.events else None
        )

    def navigate(self, index):
        anchors = [
            self.editor_panel,
            self.scheduler_panel,
            self.memory_panel,
            self.results_panel,
        ]
        target = anchors[index]
        self.scroll.verticalScrollBar().setValue(target.y() - 12)
        for i, btn in enumerate(self.menu_buttons):
            btn.setObjectName("activeMenu" if i == index else "menuButton")
            btn.style().unpolish(btn)
            btn.style().polish(btn)

    def on_algorithm_change(self, algorithm):
        self.quantum_input.setEnabled(algorithm == "Round Robin")
        self.algorithm_status.setText(
            "ROUND ROBIN" if algorithm == "Round Robin" else "PRIORITY"
        )
        self.clear_output()

    def clear_inputs(self):
        self.pid_input.clear()
        self.arrival_input.setValue(0)
        self.burst_input.setValue(5)
        self.priority_input.setValue(1)
        self.memory_input.setValue(100)

    def load_demo(self):
        self.processes = [
            {"pid": "P1", "arrival": 0, "burst": 5, "priority": 2, "memory": 120},
            {"pid": "P2", "arrival": 0, "burst": 3, "priority": 1, "memory": 80},
            {"pid": "P3", "arrival": 0, "burst": 4, "priority": 3, "memory": 160},
            {"pid": "P4", "arrival": 0, "burst": 2, "priority": 4, "memory": 100},
        ]
        self.refresh_processes()

    def add_process(self):
        pid = self.pid_input.text().strip()
        if not pid:
            QMessageBox.warning(
                self, "Missing Process ID", "Enter a Process ID such as P5."
            )
            return
        if any(p["pid"].lower() == pid.lower() for p in self.processes):
            QMessageBox.warning(
                self, "Duplicate Process", "This Process ID already exists."
            )
            return
        if len(self.processes) >= 30:
            QMessageBox.warning(self, "Limit Reached", "Maximum 30 processes.")
            return
        self.processes.append(
            {
                "pid": pid,
                "arrival": self.arrival_input.value(),
                "burst": self.burst_input.value(),
                "priority": self.priority_input.value(),
                "memory": self.memory_input.value(),
            }
        )
        self.refresh_processes()
        self.clear_inputs()

    def delete_selected(self):
        row = self.process_table.currentRow()
        if row < 0:
            QMessageBox.information(
                self, "Select a Row", "Select a process in the table first."
            )
            return
        self.processes.pop(row)
        self.refresh_processes()

    def refresh_processes(self):
        self.clear_output()
        self.process_count.setText(f"{len(self.processes):02d}")
        self.process_table.setRowCount(len(self.processes))
        for r, p in enumerate(self.processes):
            for c, value in enumerate(
                [p["pid"], p["arrival"], p["burst"], p["priority"], p["memory"]]
            ):
                item = QTableWidgetItem(str(value))
                item.setTextAlignment(Qt.AlignCenter)
                self.process_table.setItem(r, c, item)
        self.show_states(None)

    def clear_output(self):
        self.timer.stop()
        self.events = []
        self.results = []
        self.step = 0
        self.cpu_status.setText("IDLE")
        self.execution_label.setText("CPU: IDLE  |  Time: 0 ms")
        self.step_label.setText("Ready to simulate")
        self.gantt.update_data([], 0, {})
        (
            self.ram_status.setText(f"0 / {self.total_ram_input.value()} MB")
            if hasattr(self, "total_ram_input")
            else None
        )
        if hasattr(self, "memory_bar"):
            self.memory_bar.setValue(0)
            self.memory_label.setText(
                f"0 MB used / {self.total_ram_input.value()} MB total"
            )
            self.ram_detail_label.setText("No active RAM allocation")
        if hasattr(self, "result_table"):
            self.result_table.setRowCount(0)
            self.average_label.setText("Average WT: --   |   Average TAT: --")
        if hasattr(self, "state_table"):
            self.show_states(None)
        if hasattr(self, "run_btn"):
            self.update_controls()

    def start_simulation(self):
        self.timer.stop()
        try:
            events, results = simulate(
                self.processes,
                self.algorithm_input.currentText(),
                self.quantum_input.value(),
                self.total_ram_input.value(),
            )
        except ValueError as exc:
            QMessageBox.warning(self, "Simulation Input Error", str(exc))
            return
        self.events = events
        self.results = results
        self.step = 0
        self.pid_colors = {
            p["pid"]: COLORS[i % len(COLORS)] for i, p in enumerate(self.processes)
        }
        self.gantt.update_data(events, 0, self.pid_colors)
        self.refresh_view()
        self.timer.start(self.speed_input.value())
        self.update_controls()

    def toggle_pause(self):
        if not self.events or self.step >= len(self.events):
            return
        if self.timer.isActive():
            self.timer.stop()
        else:
            self.timer.start(self.speed_input.value())
        self.update_controls()

    def next_step(self):
        if not self.events or self.step >= len(self.events):
            return
        # Manual next stops autoplay; timer timeout advances automatically.
        if self.sender() == self.next_btn:
            self.timer.stop()
        self.step += 1
        self.refresh_view()
        if self.step >= len(self.events):
            self.timer.stop()
        self.update_controls()

    def reset_simulation(self):
        self.clear_output()

    def update_controls(self):
        has = bool(self.events)
        active = self.timer.isActive()
        unfinished = has and self.step < len(self.events)
        self.pause_btn.setEnabled(unfinished)
        self.next_btn.setEnabled(unfinished)
        self.reset_btn.setEnabled(has)
        self.pause_btn.setText("Pause" if active else "Resume")

    def show_states(self, event):
        self.state_table.setRowCount(len(self.processes))
        for row, p in enumerate(self.processes):
            state = event["states"].get(p["pid"], "New") if event else "Not Started"
            remaining = event["remaining"][p["pid"]] if event else p["burst"]
            for col, value in enumerate([p["pid"], state, remaining, p["memory"]]):
                item = QTableWidgetItem(str(value))
                item.setTextAlignment(Qt.AlignCenter)
                if col == 1 and state == "Running":
                    item.setForeground(
                        QColor("#0E9474" if self.theme == "light" else "#56D9AF")
                    )
                elif col == 1 and state == "Waiting for RAM":
                    item.setForeground(
                        QColor("#B46C0B" if self.theme == "light" else "#FFD18A")
                    )
                self.state_table.setItem(row, col, item)

    def show_results(self):
        self.result_table.setRowCount(len(self.results))
        for row, result in enumerate(self.results):
            for col, value in enumerate(
                [
                    result["pid"],
                    result["completion"],
                    result["turnaround"],
                    result["waiting"],
                ]
            ):
                item = QTableWidgetItem(str(value))
                item.setTextAlignment(Qt.AlignCenter)
                self.result_table.setItem(row, col, item)
        n = len(self.results)
        if n:
            avg_wt = sum(r["waiting"] for r in self.results) / n
            avg_tat = sum(r["turnaround"] for r in self.results) / n
            self.average_label.setText(
                f"Average WT: {avg_wt:.2f} ms   |   Average TAT: {avg_tat:.2f} ms"
            )

    def refresh_view(self):
        if self.step == 0 or not self.events:
            self.cpu_status.setText("READY")
            self.execution_label.setText("CPU: READY  |  Time: 0 ms")
            self.step_label.setText(f"Step 0 / {len(self.events)}")
            self.ram_status.setText(f"0 / {self.total_ram_input.value()} MB")
            self.memory_label.setText(
                f"0 MB used / {self.total_ram_input.value()} MB total"
            )
            self.memory_bar.setValue(0)
            self.ram_detail_label.setText("Simulation initialized")
            self.show_states(None)
            return
        event = self.events[self.step - 1]
        pid = event["pid"]
        self.cpu_status.setText(
            "DONE"
            if self.step == len(self.events)
            else ("IDLE" if pid == "IDLE" else "RUNNING")
        )
        self.execution_label.setText(
            f"CPU: {pid}  |  Executed: {event['start']}–{event['end']} ms"
        )
        self.step_label.setText(
            f"Step {self.step}/{len(self.events)}  •  Ready: {', '.join(event['ready']) or 'none'}  •  RAM wait: {', '.join(event['memory_wait']) or 'none'}"
        )
        total = self.total_ram_input.value()
        used = event["used_ram"]
        self.ram_status.setText(f"{used} / {total} MB")
        self.memory_label.setText(
            f"{used} MB used / {total} MB total  •  {event['free_ram']} MB free"
        )
        self.memory_bar.setValue(round(100 * used / total))
        self.ram_detail_label.setText(
            "Resident: "
            + (
                ", ".join(
                    f"{p['pid']} ({p['memory']} MB)"
                    for p in self.processes
                    if p["pid"] in event["resident"]
                )
                or "none"
            )
        )
        self.gantt.update_data(self.events, self.step, self.pid_colors)
        self.show_states(event)
        if self.step == len(self.events):
            self.show_results()
