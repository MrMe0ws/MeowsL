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

MAIN_WINDOW_STYLESHEET = """
MainWindow {
    background: transparent;
}
#mainContainer {
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

/* --- рельс навигации --- */
#rail {
    background: transparent;
    border-right: 1px solid #2e2e32;
}
#brandName {
    color: #f2f2f4;
    background: transparent;
    font-size: 13px;
    font-weight: 600;
}
#brandVersion {
    color: #6a6a70;
    background: transparent;
    font-size: 10px;
}
#navItem {
    color: #8e8e93;
    background: transparent;
    border: none;
    border-radius: 6px;
    padding: 7px 10px;
    text-align: left;
    font-size: 12px;
}
#navItem:hover {
    color: #f2f2f4;
    background-color: #2c2c30;
}
#navItem:checked {
    color: #f2f2f4;
    background-color: #26262a;
    font-weight: 600;
}

/* --- контент --- */
#contentArea {
    background: transparent;
    border: none;
}
#pane {
    background: transparent;
}
#sectionLabel {
    color: #6a6a70;
    background: transparent;
    padding: 0;
}
#divider {
    background-color: #2e2e32;
    border: none;
}
#rowTitle {
    color: #f2f2f4;
    background: transparent;
    font-size: 13px;
}
#rowSubtitle {
    color: #8e8e93;
    background: transparent;
    font-size: 11px;
}
#hint {
    color: #6a6a70;
    background: transparent;
    font-size: 11px;
}

/* --- клавиши --- */
#keycap {
    color: #f2f2f4;
    background-color: #232326;
    border: 1px solid #3a3a3e;
    border-bottom: 2px solid #3a3a3e;
    border-radius: 5px;
    padding: 3px 8px;
    min-width: 12px;
    font-size: 12px;
    font-weight: 600;
}
#keyPlus {
    color: #6a6a70;
    background: transparent;
    font-size: 11px;
}

/* --- пилюли состояния --- */
#pill {
    border-radius: 9px;
    padding: 2px 8px;
    font-size: 10px;
    font-weight: 600;
}
#pill[tone="ok"] {
    color: #5cc48f;
    border: 1px solid rgba(92, 196, 143, 100);
    background-color: rgba(92, 196, 143, 22);
}
#pill[tone="warn"] {
    color: #d9a441;
    border: 1px solid rgba(217, 164, 65, 105);
    background-color: rgba(217, 164, 65, 22);
}
#pill[tone="idle"] {
    color: #8e8e93;
    border: 1px solid #3a3a3e;
    background-color: transparent;
}

/* --- кнопки --- */
#miniBtn {
    color: #8e8e93;
    background: transparent;
    border: 1px solid #2e2e32;
    border-radius: 5px;
    padding: 4px 10px;
    font-size: 11px;
}
#miniBtn:hover {
    color: #f2f2f4;
    border-color: #4a4a52;
    background-color: #2c2c30;
}
#miniBtn:disabled {
    color: #55555c;
    border-color: #232326;
}
#linkBtn {
    color: #8e8e93;
    background: transparent;
    border: none;
    border-radius: 5px;
    padding: 5px 8px;
    font-size: 12px;
}
#linkBtn:hover {
    color: #f2f2f4;
    background-color: #2c2c30;
}
#copyBtn {
    color: rgba(255, 255, 255, 200);
    background-color: rgba(44, 44, 48, 180);
    border: none;
    border-radius: 4px;
    font-size: 12px;
    min-width: 24px;
    min-height: 22px;
}
#copyBtn:hover {
    color: #ffffff;
    background-color: #3a3a3e;
}

/* --- карточки хоткеев --- */
#keyCard {
    background-color: #1d1d20;
    border: 1px solid #2e2e32;
    border-radius: 9px;
}
#keyCard:hover {
    background-color: #212125;
    border-color: #43434a;
}
#cardCaption {
    color: #8e8e93;
    background: transparent;
    font-size: 12px;
}

/* --- статус --- */
#statusTitle {
    color: #f2f2f4;
    background: transparent;
    font-size: 14px;
    font-weight: 600;
}
#statusDetail {
    color: #8e8e93;
    background: transparent;
    font-size: 12px;
}

/* --- строки истории --- */
#historyRow {
    background: transparent;
    border: none;
    border-radius: 7px;
}
#historyRow:hover {
    background-color: #212125;
}
#historySource {
    color: #8e8e93;
    background: transparent;
    font-size: 12px;
}
#historyTarget {
    color: #f2f2f4;
    background: transparent;
    font-size: 12px;
}
#historyArrow {
    color: #6a6a70;
    background: transparent;
    font-size: 11px;
}
#historyClock {
    color: #6a6a70;
    background: transparent;
    font-size: 10px;
}
#emptyState {
    color: #6a6a70;
    background: transparent;
    font-size: 12px;
}

/* --- поля выбора --- */
QComboBox {
    color: #f2f2f4;
    background-color: #232326;
    border: 1px solid #3a3a3e;
    border-radius: 6px;
    padding: 4px 8px;
    font-size: 12px;
    min-width: 140px;
}
QComboBox:hover {
    border-color: #4a4a52;
}
QComboBox::drop-down {
    border: none;
    width: 20px;
}
QComboBox::down-arrow {
    image: none;
    width: 0;
    height: 0;
}
QComboBox QAbstractItemView {
    color: #f2f2f4;
    background-color: #232326;
    border: 1px solid #3a3a3e;
    border-radius: 6px;
    padding: 4px;
    outline: none;
    selection-background-color: #3d5a80;
    selection-color: #ffffff;
}

/* --- подвал --- */
#mainFooter {
    background: transparent;
    border-top: 1px solid #2e2e32;
}
#footerVersion {
    color: #6a6a70;
    background: transparent;
    font-size: 11px;
}

/* --- прокрутка --- */
QScrollArea {
    background: transparent;
    border: none;
}
QScrollArea > QWidget > QWidget {
    background: transparent;
}
QScrollBar:vertical {
    background: transparent;
    width: 7px;
    margin: 4px 2px 4px 0;
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

/* --- всплывающее уведомление --- */
#toast {
    color: #f2f2f4;
    background-color: #26262b;
    border: 1px solid #3a3a42;
    border-radius: 8px;
    padding: 8px 14px;
    font-size: 12px;
}

/* --- диалог захвата клавиши --- */
#captureDialog {
    background-color: #1a1a1c;
    border: 1px solid #2e2e32;
    border-radius: 12px;
}
#captureTitle {
    color: #f2f2f4;
    background: transparent;
    font-size: 15px;
    font-weight: 600;
}
#captureHint {
    color: #8e8e93;
    background: transparent;
    font-size: 12px;
}
#captureKey {
    color: #f2f2f4;
    background-color: #232326;
    border: 1px solid #3a3a3e;
    border-bottom: 2px solid #3a3a3e;
    border-radius: 8px;
    padding: 10px 18px;
    font-size: 18px;
    font-weight: 600;
}
"""
