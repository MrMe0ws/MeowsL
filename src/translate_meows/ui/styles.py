"""QSS-стили для UI."""

POPUP_STYLESHEET = """
TranslationPopup {
    background: transparent;
}
#container {
    background-color: #1a1a1c;
    border: 1px solid #2e2e32;
    border-radius: 12px;
}
#titleBar {
    background-color: transparent;
    border: none;
}
#appTitle {
    color: #a8a8ad;
    background: transparent;
    border: none;
    padding: 0;
}
#headerBtn {
    color: #8e8e93;
    background: transparent;
    border: none;
    border-radius: 6px;
    font-size: 15px;
    padding: 2px 6px;
    min-width: 26px;
    min-height: 26px;
}
#headerBtn:hover {
    color: #ffffff;
    background-color: #2c2c30;
}
#closeBtn {
    color: #8e8e93;
    background: transparent;
    border: none;
    border-radius: 6px;
    font-size: 18px;
    padding: 0 6px;
    min-width: 26px;
    min-height: 26px;
}
#closeBtn:hover {
    color: #ffffff;
    background-color: #3a2a2a;
}
#fieldDivider {
    background-color: #2e2e32;
    border: none;
    max-height: 1px;
    min-height: 1px;
}
#textPanel {
    background-color: #1a1a1c;
    border: none;
}
#langBadge {
    color: rgba(255, 255, 255, 90);
    background: transparent;
    border: none;
    padding: 0;
}
QTextEdit#input, QTextEdit#output {
    color: #f2f2f4;
    background-color: transparent;
    border: none;
    border-radius: 0;
    padding: 28px 16px 14px 16px;
    selection-background-color: #3d5a80;
    selection-color: #ffffff;
}
QTextEdit#input:focus, QTextEdit#output:focus {
    background-color: rgba(255, 255, 255, 8);
}
#copyIcon {
    color: rgba(255, 255, 255, 200);
    background-color: rgba(44, 44, 48, 180);
    border: none;
    border-radius: 4px;
    font-size: 12px;
    padding: 0;
}
#copyIcon:hover {
    color: #ffffff;
    background-color: rgba(58, 58, 62, 220);
}
QScrollBar:vertical {
    background: transparent;
    width: 7px;
    margin: 8px 3px 8px 0;
    border: none;
}
QScrollBar::handle:vertical {
    background: #3a3a3e;
    border-radius: 3px;
    min-height: 28px;
}
QScrollBar::handle:vertical:hover {
    background: #4a4a4e;
}
QScrollBar::add-line:vertical,
QScrollBar::sub-line:vertical {
    height: 0;
    border: none;
    background: none;
}
QScrollBar::add-page:vertical,
QScrollBar::sub-page:vertical {
    background: none;
}
QScrollBar:horizontal {
    background: transparent;
    height: 7px;
    margin: 0 8px 3px 8px;
    border: none;
}
QScrollBar::handle:horizontal {
    background: #3a3a3e;
    border-radius: 3px;
    min-width: 28px;
}
QScrollBar::handle:horizontal:hover {
    background: #4a4a4e;
}
QScrollBar::add-line:horizontal,
QScrollBar::sub-line:horizontal {
    width: 0;
    border: none;
    background: none;
}
QScrollBar::add-page:horizontal,
QScrollBar::sub-page:horizontal {
    background: none;
}
"""
