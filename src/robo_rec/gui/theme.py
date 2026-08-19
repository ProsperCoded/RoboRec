"""Design tokens and the QSS stylesheet for Robo-Rec's dark, instrument-panel theme."""

from __future__ import annotations

BG = "#0E1214"
SURFACE = "#161B1E"
SURFACE_RAISED = "#1C2226"
SIDEBAR = "#0A0D0F"
BORDER = "#262D31"
BORDER_STRONG = "#333C41"
TEXT_PRIMARY = "#E8ECEE"
TEXT_SECONDARY = "#8A9499"
TEXT_MUTED = "#5C6569"
ACCENT = "#4FD1A5"
ACCENT_DIM = "#2E4A40"
WARNING = "#E0A458"
WARNING_DIM = "#4A3D2A"
DANGER = "#E07B7B"

FONT_UI = '"Segoe UI", "SF Pro Text", "Helvetica Neue", Arial, sans-serif'
FONT_MONO = '"Cascadia Code", "SF Mono", "Consolas", "DejaVu Sans Mono", monospace'

STYLESHEET = f"""
QWidget {{
    background-color: {BG};
    color: {TEXT_PRIMARY};
    font-family: {FONT_UI};
    font-size: 13px;
}}

QMainWindow, #ContentArea {{
    background-color: {BG};
}}

/* ---- Sidebar ---- */
#Sidebar {{
    background-color: {SIDEBAR};
    border-right: 1px solid {BORDER};
}}

#SidebarBrand {{
    color: {TEXT_PRIMARY};
    font-size: 13px;
    font-weight: 700;
    letter-spacing: 1.5px;
    padding-left: 8px;
}}

#SidebarNavItem {{
    background-color: transparent;
    border: 1px solid transparent;
    border-radius: 8px;
    color: {TEXT_SECONDARY};
    font-weight: 600;
    font-size: 13px;
    text-align: left;
    padding-left: 8px;
}}

#SidebarNavItem:checked {{
    background-color: {ACCENT_DIM};
    border: 1px solid {ACCENT};
    color: {ACCENT};
}}

#SidebarNavItem:hover {{
    color: {TEXT_PRIMARY};
    border: 1px solid {BORDER_STRONG};
}}

#SidebarNavItem:pressed {{
    background-color: {ACCENT_DIM};
}}

/* ---- Top status bar ---- */
#TopBar {{
    background-color: {BG};
    border-bottom: 1px solid {BORDER};
}}

#AppTitle {{
    font-size: 15px;
    font-weight: 600;
    color: {TEXT_PRIMARY};
}}

#GpuBadge {{
    border-radius: 11px;
}}

#GpuBadge QLabel {{
    background: transparent;
    font-size: 11px;
    font-weight: 600;
    letter-spacing: 0.5px;
}}

#GpuBadge[state="detected"] {{
    background-color: {ACCENT_DIM};
    border: 1px solid {ACCENT};
}}

#GpuBadge[state="detected"] QLabel {{
    color: {ACCENT};
}}

#GpuBadge[state="unavailable"] {{
    background-color: {SURFACE_RAISED};
    border: 1px solid {BORDER_STRONG};
}}

#GpuBadge[state="unavailable"] QLabel {{
    color: {TEXT_SECONDARY};
}}

/* ---- Dashboard ---- */
#DashboardTitle {{
    font-size: 22px;
    font-weight: 600;
    color: {TEXT_PRIMARY};
}}

#DashboardSubtitle {{
    font-size: 13px;
    color: {TEXT_SECONDARY};
}}

/* ---- Action card ---- */
ActionCard {{
    background-color: {SURFACE};
    border: 1px solid {BORDER};
    border-radius: 12px;
}}

ActionCard:hover {{
    border: 1px solid {ACCENT};
    background-color: {SURFACE_RAISED};
}}

#CardTitle {{
    font-size: 15px;
    font-weight: 600;
    color: {TEXT_PRIMARY};
}}

#CardDescription {{
    font-size: 12px;
    color: {TEXT_SECONDARY};
}}

#CardGlyph {{
    background: transparent;
}}

/* ---- Panels ---- */
#PanelHeader {{
    font-size: 18px;
    font-weight: 600;
    color: {TEXT_PRIMARY};
}}

#PanelSubtitle {{
    font-size: 12px;
    color: {TEXT_SECONDARY};
}}

#BreadcrumbButton {{
    background-color: transparent;
    border: none;
    color: {TEXT_SECONDARY};
    font-size: 12px;
    padding: 4px 0px;
    text-align: left;
}}

#BreadcrumbButton:hover {{
    color: {ACCENT};
}}

#SectionLabel {{
    font-size: 11px;
    font-weight: 600;
    letter-spacing: 0.8px;
    color: {TEXT_MUTED};
    text-transform: uppercase;
}}

QGroupBox {{
    background-color: {SURFACE};
    border: 1px solid {BORDER};
    border-radius: 10px;
    margin-top: 8px;
    padding-top: 14px;
}}

QGroupBox::title {{
    subcontrol-origin: margin;
    left: 12px;
    padding: 0 4px;
    color: {TEXT_SECONDARY};
    font-size: 11px;
    font-weight: 600;
    letter-spacing: 0.6px;
}}

/* ---- Seed tile (signature element) ---- */
SeedTile {{
    background-color: {SURFACE_RAISED};
    border: 1px solid {BORDER};
    border-radius: 6px;
}}

SeedTile:hover {{
    border: 1px solid {BORDER_STRONG};
    background-color: {SURFACE};
}}

SeedTile[filled="true"] {{
    border: 1px solid {BORDER_STRONG};
}}

SeedTile[filled="true"]:hover {{
    border: 1px solid {ACCENT};
}}

SeedTile[blank="true"] {{
    border: 1px dashed {WARNING};
    background-color: {WARNING_DIM};
}}

SeedTile[blank="true"]:hover {{
    border: 1px solid {WARNING};
}}

#SeedTileIndex {{
    font-family: {FONT_MONO};
    font-size: 9px;
    color: {TEXT_MUTED};
}}

#SeedTileWord {{
    font-family: {FONT_MONO};
    font-size: 12px;
    color: {TEXT_PRIMARY};
    background: transparent;
    border: none;
}}

/* ---- Inputs ---- */
QComboBox, QLineEdit, QSpinBox {{
    background-color: {SURFACE_RAISED};
    border: 1px solid {BORDER};
    border-radius: 6px;
    padding: 6px 8px;
    color: {TEXT_PRIMARY};
    selection-background-color: {ACCENT_DIM};
}}

QComboBox:hover, QLineEdit:hover, QSpinBox:hover {{
    border: 1px solid {BORDER_STRONG};
}}

QComboBox:focus, QLineEdit:focus, QSpinBox:focus {{
    border: 1px solid {ACCENT};
}}

QComboBox::drop-down {{
    border: none;
    width: 20px;
}}

QComboBox QAbstractItemView {{
    background-color: {SURFACE_RAISED};
    border: 1px solid {BORDER_STRONG};
    selection-background-color: {ACCENT_DIM};
    selection-color: {ACCENT};
    outline: none;
}}

QRadioButton, QCheckBox {{
    color: {TEXT_PRIMARY};
    spacing: 8px;
}}

QRadioButton:hover, QCheckBox:hover {{
    color: {ACCENT};
}}

/* ---- Buttons ---- */
QPushButton {{
    background-color: {SURFACE_RAISED};
    border: 1px solid {BORDER_STRONG};
    border-radius: 6px;
    padding: 8px 16px;
    color: {TEXT_PRIMARY};
    font-weight: 500;
}}

QPushButton:hover {{
    border: 1px solid {ACCENT};
    background-color: {SURFACE};
}}

QPushButton:pressed {{
    background-color: {ACCENT_DIM};
}}

QPushButton:disabled {{
    color: {TEXT_MUTED};
    border: 1px solid {BORDER};
    background-color: {SURFACE_RAISED};
}}

QPushButton#PrimaryButton {{
    background-color: {ACCENT_DIM};
    border: 1px solid {ACCENT};
    color: {ACCENT};
}}

QPushButton#PrimaryButton:hover {{
    background-color: {ACCENT};
    color: {SIDEBAR};
}}

QPushButton#PrimaryButton:pressed {{
    background-color: {ACCENT};
    border: 1px solid {TEXT_PRIMARY};
}}

QPushButton#PrimaryButton:disabled {{
    background-color: {SURFACE_RAISED};
    border: 1px solid {BORDER};
    color: {TEXT_MUTED};
}}

#BreadcrumbButton:pressed {{
    color: {ACCENT};
}}

/* ---- Notices ---- */
#WarningNotice {{
    background-color: {WARNING_DIM};
    border: 1px solid {WARNING};
    border-radius: 8px;
    color: {WARNING};
    padding: 10px 12px;
    font-size: 12px;
}}

#InfoNotice {{
    background-color: {SURFACE_RAISED};
    border: 1px solid {BORDER_STRONG};
    border-radius: 8px;
    color: {TEXT_SECONDARY};
    padding: 10px 12px;
    font-size: 12px;
}}

QProgressBar {{
    background-color: {SURFACE_RAISED};
    border: 1px solid {BORDER};
    border-radius: 4px;
}}

QProgressBar::chunk {{
    background-color: {ACCENT};
    border-radius: 4px;
}}

QScrollBar:vertical {{
    background: transparent;
    width: 10px;
}}

QScrollBar::handle:vertical {{
    background: {BORDER_STRONG};
    border-radius: 5px;
    min-height: 24px;
}}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0px;
}}
"""
