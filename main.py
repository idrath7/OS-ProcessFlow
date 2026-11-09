import sys
from PySide6.QtWidgets import QApplication, QMainWindow
from dashboard import Dashboard
from styles import get_style


class ProcessFlowApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("OS ProcessFlow | CPU Scheduling & Memory Simulator")
        self.resize(1490, 910)
        self.setMinimumSize(1180, 720)
        self.setCentralWidget(Dashboard())


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyleSheet(get_style("light"))
    window = ProcessFlowApp()
    window.show()
    sys.exit(app.exec())
