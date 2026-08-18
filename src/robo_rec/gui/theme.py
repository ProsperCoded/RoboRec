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

#SidebarActionsTab {{
    background-color: transparent;
    border: 1px solid transparent;
    border-radius: 8px;
    color: {TEXT_SECONDARY};
    font-weight: 600;
    letter-spacing: 1px;
    padding: 10px 6px;
}}

#SidebarActionsTab:checked {{
    background-color: {ACCENT_DIM};
    border: 1px solid {ACCENT};
    color: {ACCENT};
}}

#SidebarActionsTab:hover {{
    color: {TEXT_PRIMARY};
    border: 1px solid {BORDER_STRONG};
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
    padding: 4px 12px;
    font-size: 11px;
    font-weight: 600;
    letter-spacing: 0.5px;
}}

#GpuBadge[state="detected"] {{
    background-color: {ACCENT_DIM};
    color: {ACCENT};
    border: 1px solid {ACCENT};
}}

#GpuBadge[state="unavailable"] {{
    background-color: {SURFACE_RAISED};
    color: {TEXT_SECONDARY};
    border: 1px solid {BORDER_STRONG};
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
    font-size: 20px;
    color: {ACCENT};
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

SeedTile[filled="true"] {{
    border: 1px solid {BORDER_STRONG};
}}

SeedTile[blank="true"] {{
    border: 1px dashed {WARNING};
    background-color: {WARNING_DIM};
}}

#SeedTileIndex {{
    font-family: {FONT_MONO};
    font-size: 9px;
    color: {TEXT_MUTED};
}}

#SeedTileWord {{
    font-family: {FONT_MONO};
    font-size: 13px;
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

QComboBox:focus, QLineEdit:focus, QSpinBox:focus {{
    border: 1px solid {ACCENT};
}}

QComboBox::drop-down {{
    border: none;
    width: 20px;
}}

QRadioButton, QCheckBox {{
    color: {TEXT_PRIMARY};
    spacing: 8px;
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
}}

QPushButton:disabled {{
    color: {TEXT_MUTED};
    border: 1px solid {BORDER};
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

QPushButton#PrimaryButton:disabled {{
    background-color: {SURFACE_RAISED};
    border: 1px solid {BORDER};
    color: {TEXT_MUTED};
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
