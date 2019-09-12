from typing import List

from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QMessageBox, QLabel, QWidget, QHBoxLayout
from bauh.api.abstract.view import MessageType

from bauh.util import resource

MSG_TYPE_MAP = {
    MessageType.ERROR: QMessageBox.Critical,
    MessageType.INFO: QMessageBox.Information,
    MessageType.WARNING: QMessageBox.Warning
}


def show_message(title: str, body: str, type_: MessageType, icon: QIcon = QIcon(resource.get_path('img/logo.svg'))):
    popup = QMessageBox()
    popup.setWindowTitle(title)
    popup.setText(body)
    popup.setIcon(MSG_TYPE_MAP[type_])

    if icon:
        popup.setWindowIcon(icon)

    popup.exec_()


def ask_confirmation(title: str, body: str, locale_keys: dict, icon: QIcon = QIcon(resource.get_path('img/logo.svg')), widgets: List[QWidget] = None):
    diag = QMessageBox()
    diag.setIcon(QMessageBox.Question)
    diag.setWindowTitle(title)
    diag.setStyleSheet('QLabel { margin-right: 25px; }')

    wbody = QWidget()
    wbody.setLayout(QHBoxLayout())
    wbody.layout().addWidget(QLabel(body))

    if widgets:
        for w in widgets:
            wbody.layout().addWidget(w)

    diag.layout().addWidget(wbody, 0, 1)

    bt_yes = diag.addButton(locale_keys['popup.button.yes'], QMessageBox.YesRole)

    diag.addButton(locale_keys['popup.button.no'], QMessageBox.NoRole)

    if icon:
        diag.setWindowIcon(icon)

    diag.exec_()

    return diag.clickedButton() == bt_yes
