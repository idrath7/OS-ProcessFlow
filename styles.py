"""High-contrast, accessible palettes. No external font downloads required."""

LIGHT = {
    "canvas": "#F4F7FB",
    "sidebar": "#101D33",
    "side_border": "#243854",
    "surface": "#FFFFFF",
    "surface_alt": "#F7F9FC",
    "line": "#DDE5F0",
    "title": "#15263E",
    "body": "#33465E",
    "muted": "#596D84",
    "accent": "#3159D8",
    "accent_hover": "#244AC6",
    "accent_soft": "#EDF2FF",
    "input": "#FFFFFF",
    "table_alt": "#F4F7FC",
    "table_header": "#EAF0F8",
    "track": "#E7EDF5",
    "future": "#DFE7F2",
    "success": "#0B8469",
    "warning": "#B46C0B",
    "danger_bg": "#FFF0F0",
    "danger_text": "#B4233B",
    "secondary_bg": "#E8EEF8",
    "secondary_hover": "#DCE6F6",
    "side_text": "#CBD6E7",
    "side_muted": "#91A5BE",
}
DARK = {
    "canvas": "#0D1525",
    "sidebar": "#0A1220",
    "side_border": "#253650",
    "surface": "#18263B",
    "surface_alt": "#132135",
    "line": "#30425A",
    "title": "#F6F9FE",
    "body": "#E1EAF7",
    "muted": "#B1C1D4",
    "accent": "#4D79EF",
    "accent_hover": "#6691FF",
    "accent_soft": "#243C6D",
    "input": "#101C2E",
    "table_alt": "#203149",
    "table_header": "#293D58",
    "track": "#0E1B2D",
    "future": "#36455C",
    "success": "#53D7AE",
    "warning": "#FFD18A",
    "danger_bg": "#4D283A",
    "danger_text": "#FFD1D9",
    "secondary_bg": "#2B405E",
    "secondary_hover": "#3A5273",
    "side_text": "#D4E1F1",
    "side_muted": "#91A5BE",
}


def get_style(theme="light"):
    c = LIGHT if theme == "light" else DARK
    return f"""
    QWidget {{ font-family: 'Segoe UI'; font-size: 14px; color: {c['body']}; }}
    QMainWindow, QWidget#mainBody {{ background-color: {c['canvas']}; }}
    QFrame#sidebar {{ background-color: {c['sidebar']}; border: none;
        border-right: 1px solid {c['side_border']}; }}
    QLabel#logo {{ color: #FFFFFF; font-size: 21px; font-weight: bold; }}
    QLabel#brandSubtitle {{ color: {c['side_muted']}; font-size: 12px; }}
    QLabel#versionText {{ color: {c['side_muted']}; font-size: 12px; }}
    QPushButton#menuButton, QPushButton#activeMenu {{ text-align: left;
        border: none; border-radius: 10px; min-height: 42px;
        padding-left: 17px; padding-right: 8px; font-size: 14px; }}
    QPushButton#menuButton {{ background: transparent; color: {c['side_text']}; }}
    QPushButton#menuButton:hover {{ background-color: #243957; color: #FFFFFF; }}
    QPushButton#activeMenu {{ background-color: #365FD9; color: #FFFFFF; font-weight: bold; }}
    QPushButton#themeButton {{ background-color: #203451; color: #FFFFFF;
        border: 1px solid #3B5272; text-align: center; border-radius: 10px;
        min-height: 38px; font-size: 13px; padding: 6px 10px; }}
    QPushButton#themeButton:hover {{ background-color: #2D496E; }}
    QLabel#pageTitle {{ color: {c['title']}; font-size: 31px; font-weight: bold; }}
    QLabel#pageSubtitle {{ color: {c['muted']}; font-size: 14px; }}
    QLabel#sectionTitle {{ color: {c['title']}; font-size: 19px; font-weight: bold; }}
    QLabel#muted {{ color: {c['muted']}; font-size: 13px; }}
    QLabel#cardTitle {{ color: {c['muted']}; font-size: 12px; font-weight: bold; }}
    QLabel#cardValue {{ color: {c['title']}; font-size: 23px; font-weight: bold; }}
    QFrame#panel, QFrame#statusCard {{ background-color: {c['surface']};
        border: 1px solid {c['line']}; border-radius: 14px; }}
    QPushButton {{ border: none; border-radius: 9px; min-height: 40px;
        padding: 6px 16px; font-size: 14px; font-weight: bold; }}
    QPushButton#primaryButton {{ background-color: {c['accent']}; color: #FFFFFF; }}
    QPushButton#primaryButton:hover {{ background-color: {c['accent_hover']}; }}
    QPushButton#secondaryButton {{ background-color: {c['secondary_bg']}; color: {c['title']}; }}
    QPushButton#secondaryButton:hover {{ background-color: {c['secondary_hover']}; }}
    QPushButton#dangerButton {{ background-color: {c['danger_bg']}; color: {c['danger_text']};
        border: 1px solid {c['line']}; }}
    QPushButton:disabled {{ background-color: {c['track']}; color: {c['muted']}; }}
    QLineEdit, QSpinBox, QComboBox {{ background-color: {c['input']}; color: {c['title']};
        border: 1px solid {c['line']}; border-radius: 9px; min-height: 33px;
        padding: 6px 12px; font-size: 14px; selection-background-color: {c['accent']}; }}
    QLineEdit:focus, QSpinBox:focus, QComboBox:focus {{ border: 2px solid {c['accent']}; }}
    QSpinBox:disabled, QComboBox:disabled {{ color: {c['muted']}; background-color: {c['track']}; }}
    QComboBox::drop-down {{ width: 26px; border: none; }}
    QComboBox QAbstractItemView {{ background-color: {c['surface']}; color: {c['title']};
        border: 1px solid {c['line']}; selection-background-color: {c['accent']}; }}
    QTableWidget {{ background-color: {c['surface']}; alternate-background-color: {c['table_alt']};
        color: {c['title']}; border: 1px solid {c['line']}; border-radius: 10px;
        gridline-color: {c['line']}; selection-background-color: {c['accent_soft']};
        selection-color: {c['title']}; font-size: 14px; outline: none; }}
    QTableWidget::item {{ padding: 8px; }}
    QHeaderView::section {{ background-color: {c['table_header']}; color: {c['title']};
        border: none; border-bottom: 1px solid {c['line']};
        padding: 12px 7px; font-size: 13px; font-weight: bold; }}
    QTableCornerButton::section {{ background-color: {c['table_header']}; border: none; }}
    QProgressBar {{ background-color: {c['track']}; color: {c['title']};
        border: 1px solid {c['line']}; border-radius: 8px; text-align: center;
        min-height: 28px; font-size: 13px; font-weight: bold; }}
    QProgressBar::chunk {{ background-color: #1CA78B; border-radius: 7px; }}
    QScrollArea {{ background: transparent; border: none; }}
    QScrollBar:vertical {{ background-color: {c['canvas']}; width: 11px; margin: 0px; }}
    QScrollBar::handle:vertical {{ background-color: {c['line']}; min-height: 32px; border-radius: 5px; }}
    QScrollBar:horizontal {{ background-color: {c['canvas']}; height: 11px; margin: 0px; }}
    QScrollBar::handle:horizontal {{ background-color: {c['line']}; min-width: 32px; border-radius: 5px; }}
    QScrollBar::add-line, QScrollBar::sub-line {{ height: 0px; width: 0px; }}
    QToolTip {{ background-color: {c['surface']}; color: {c['title']};
        border: 1px solid {c['line']}; padding: 6px; }}
    """


APP_STYLE = get_style("light")
