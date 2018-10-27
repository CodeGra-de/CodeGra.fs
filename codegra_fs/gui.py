#!/usr/bin/env python
# SPDX-License-Identifier: AGPL-3.0-only

import os
import abc
import sys
import json
import time
import typing as t
import logging
import threading

import codegra_fs
import codegra_fs.cgfs as cgfs
import codegra_fs.constants as constants
from appdirs import AppDirs  # type: ignore
from PyQt5.QtCore import Qt, QObject, pyqtSignal  # type: ignore
from PyQt5.QtWidgets import (  # type: ignore
    QFrame, QLabel, QStyle, QDialog, QWidget, QCheckBox, QGroupBox, QLineEdit,
    QSplitter, QFileDialog, QFormLayout, QHBoxLayout, QMessageBox, QPushButton,
    QSizePolicy, QSpacerItem, QToolButton, QTreeWidget, QVBoxLayout,
    QApplication, QInputDialog, QRadioButton, QDesktopWidget, QPlainTextEdit
)

try:
    import fuse  # type: ignore
except ImportError:
    pass

PREVIOUS_VALUES_PATH = ''  # type : str


class ValueObject:
    @property
    @abc.abstractmethod
    def value(self):
        raise NotImplementedError


class CGFSRadioSelect(QHBoxLayout, ValueObject):
    def __init__(self, options: t.List[str], default) -> None:
        super().__init__()

        self.__buttons = []  # type: t.List[QRadioButton]
        for option in options:
            but = QRadioButton(option)
            self.__buttons.append((but, option))
            self.addWidget(but)
            if option == default:
                but.setChecked(True)

    @property
    def value(self):
        for but, val in self.__buttons:
            if but.isChecked():
                return val


class DirectoryButton(QHBoxLayout, ValueObject):
    def __init__(self, window: QWidget, default: t.Optional[str]) -> None:
        super().__init__()
        self.__label = QLineEdit(window)

        def on_click() -> None:
            options = QFileDialog.Options()
            options |= QFileDialog.ShowDirsOnly
            options |= QFileDialog.DontResolveSymlinks
            value = QFileDialog.getExistingDirectory(
                window, "Mount directory", "~", options
            )
            self.__label.setText(value)

        self.__button = QPushButton('Browse')
        self.__button.clicked.connect(on_click)

        if default is not None:
            self.__label.setText(default)

        self.addWidget(self.__label)
        self.addWidget(self.__button)

    @property
    def value(self) -> str:
        return self.__label.text()


class StringInput(QLineEdit, ValueObject):
    def __init__(self, is_password: bool=False,
                 default: t.Optional[str]=None) -> None:
        super().__init__()
        if is_password:
            self.setEchoMode(QLineEdit.Password)
        if default is not None:
            self.setText(default)

    @property
    def value(self) -> str:
        return self.text()


class CheckBoxInput(QCheckBox, ValueObject):
    def __init__(
        self,
        default: bool=False,
    ) -> None:
        super().__init__()
        self.tooltip = 'Hello'
        if default is not None:
            self.setChecked(default)

    @property
    def value(self) -> str:
        return self.isChecked()


class CGFSFormLayout(QFormLayout):
    def add_help_row(self, a, b, help_text):
        wrapper = QWidget()

        layout = QHBoxLayout(wrapper)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.setAlignment(Qt.AlignTop)

        if isinstance(a, str):
            a = QLabel(a)
        layout.addWidget(a)

        help_button = QToolButton()
        help_button.setIcon(
            QApplication.style()
            .standardIcon(QStyle.SP_TitleBarContextHelpButton)
        )
        layout.addWidget(help_button)
        help_button.setStyleSheet('margin-left: 5px;')

        help_label = QLabel(help_text)
        help_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        help_label.hide()
        help_button.clicked.connect(
            lambda: help_label.setVisible(not help_label.isVisible())
        )
        help_label.setStyleSheet("border: 1px solid gray; padding: 5px;")

        if isinstance(b, QWidget):
            wrap = QWidget()
            l = QHBoxLayout(wrap)
            l.addWidget(b)
            l.setContentsMargins(0, 0, 0, 0)
            l.setSpacing(0)
            b = wrap

        self.addRow(wrapper, b)
        self.addRow(help_label)


class CGFSLoggingWindow(QPlainTextEdit):
    signal = pyqtSignal(str)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.setReadOnly(True)
        outer_self = self

        class QTextEditLogger(logging.Handler):
            def __init__(self):
                super().__init__()

            def emit(self, record):
                msg = self.format(record)
                outer_self.signal.emit(msg)

        self.log_handler = QTextEditLogger

        def connector(msg):
            self.appendPlainText(msg)

        self.signal.connect(connector)

    def set_logging_level(self, level) -> None:
        logging.basicConfig(
            level=level,
            format=
            '%(asctime)-10s - %(module)-8s - %(levelname)-8s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S',
            handlers=[self.log_handler()]
        )


class CGFSUi(QWidget):
    def __init__(self) -> None:
        super().__init__()

        self.setWindowTitle('CodeGra.fs')
        self.__fields = {}  # type: t.Dict[str, ValueObject]

        layout = QVBoxLayout()
        err = codegra_fs.utils.get_fuse_install_message()
        if err:
            msg, url = err
            if url:
                msg += '\nYou can download it <a href="{}">here</a>.'.format(
                    url
                )
            error_label = QLabel(msg)
            error_label.setTextFormat(Qt.RichText)
            error_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
            error_label.setTextInteractionFlags(Qt.TextBrowserInteraction)
            error_label.setOpenExternalLinks(True)
            layout.addWidget(error_label)
        else:
            start_form = self.__create_start_form()
            run_dialog = self.__create_run_dialog()
            run_dialog.hide()
            layout.addWidget(start_form)
            layout.addWidget(run_dialog)

        self.setLayout(layout)

        width = 800
        height = 800
        top = 40
        left = 40

        self.setGeometry(left, top, width, height)
        self.__run_thread = None  # type: t.Optional[threading.Thread]
        self.show()

    def __check_options(self) -> t.List[str]:
        err = []
        f = self.__fields
        if not f['username'].value:
            err.append('The username cannot be empty')
        if not f['password'].value:
            err.append('The password cannot be empty')
        if not f['url'].value:
            err.append('The url cannot be empty')
        mp = f['mountpoint'].value
        if not mp or not os.path.isdir(mp) or os.listdir(mp):
            err.append(
                'The mount directory should be an empty existing folder'
            )
        return err

    def __start_cgfs(self) -> None:
        errs = self.__check_options()
        if errs:
            self.__errs_field.setText(
                '\n'.join('- {}'.format(e) for e in errs)
            )
            self.__errs_field.setVisible(True)
            return
        self.__errs_field.setVisible(False)

        if self.__fields['verbosity'].value == 'quiet':
            level = logging.WARNING
        elif self.__fields['verbosity'].value == 'verbose':
            level = logging.DEBUG
        else:
            level = logging.INFO
        self.__log_window.clear()
        self.__log_window.set_logging_level(level)

        def thread():
            f = self.__fields
            with open(PREVIOUS_VALUES_PATH, 'w') as file:
                json.dump(
                    {k: v.value
                     for k, v in f.items() if k != 'password'}, file
                )
            mountpoint = f['mountpoint'].value
            if sys.platform.startswith('win32'):
                mountpoint = os.path.join(mountpoint, 'codegrade')
            cgfs.create_and_mount_fs(
                username=f['username'].value,
                password=f['password'].value,
                url=f['url'].value,
                fixed=f['fixed'].value,
                assigned_only=f['assigned_only'].value,
                latest_only=not f['all_submissions'].value,
                mountpoint=mountpoint,
                rubric_append_only=True,
            )

        self.__run_thread = threading.Thread(target=thread)
        self.__run_thread.start()
        self.__form_wrapper.setVisible(False)
        self.__run_wrapper.setVisible(True)

    def stop_cgfs(self) -> None:
        if cgfs.fuse_ptr is not None:
            fuse._libfuse.fuse_exit(cgfs.fuse_ptr)
            try:
                # Kick fuse
                os.listdir(self.__fields['mountpoint'].value)
            except BaseException:
                pass
        cgfs.fuse_ptr = None

        if self.__run_thread:
            self.__run_thread.join()
        self.__run_thread = None

        self.__form_wrapper.setVisible(True)
        self.__run_wrapper.setVisible(False)

    def __create_run_dialog(self) -> QWidget:
        stop_button = QPushButton('Stop!')
        stop_button.clicked.connect(self.stop_cgfs)
        wrapper = QWidget()
        res = QVBoxLayout(wrapper)
        self.__log_window = CGFSLoggingWindow()
        res.addWidget(self.__log_window)
        res.addWidget(stop_button)
        self.__run_wrapper = wrapper
        return wrapper

    def __create_start_form(self) -> QWidget:
        try:
            with open(PREVIOUS_VALUES_PATH, 'r') as f:
                prev_values = json.load(f)
        except:
            prev_values = {}

        form = CGFSFormLayout()

        fields = {
            'username':
                StringInput(default=prev_values.get('username')),
            'password':
                StringInput(is_password=True),
            'url':
                StringInput(
                    default=os.getenv(
                        'CGAPI_BASE_URL', prev_values.get('url')
                    )
                ),
            'fixed':
                CheckBoxInput(prev_values.get('fixed')),
            'assigned_only':
                CheckBoxInput(prev_values.get('assigned_only')),
            'mountpoint':
                DirectoryButton(self, prev_values.get('mountpoint')),
            'all_submissions':
                CheckBoxInput(prev_values.get('all_submissions')),
            'verbosity':
                CGFSRadioSelect(
                    ['verbose', 'normal', 'quiet'],
                    prev_values.get('verbosity', 'normal')
                ),
        }  # type: t.Dict[str, ValueObject]

        form.add_help_row(
            'Username *', fields['username'], 'Your CodeGra.de username'
        )
        form.add_help_row(
            'Password *', fields['password'], constants.password_help
        )
        form.add_help_row('URL *', fields['url'], constants.url_help)

        form.add_help_row(
            'Fixed mode', fields['fixed'], constants.fixed_mode_help
        )
        form.add_help_row(
            'Assigned only', fields['assigned_only'],
            constants.assigned_only_help
        )
        form.add_help_row(
            'All submissions', fields['all_submissions'],
            constants.all_submissions_help
        )
        form.add_help_row(
            'Verbosity *', fields['verbosity'], (
                "Amount of log output displayed. Set to "
                "'verbose' when reporting bugs."
            )
        )
        form.add_help_row(
            'Mount directory *',
            fields['mountpoint'],
            constants.mountpoint_help,
        )

        form.addItem(
            QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)
        )
        form.addRow(QLabel('* indicates a required field'))

        self.__errs_field = QLabel()
        self.__errs_field.setVisible(False)
        self.__errs_field.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.__errs_field.setStyleSheet(
            'border: 1px solid red; background: white; padding: 5px;'
        )

        start_button = QPushButton('Mount!')
        start_button.clicked.connect(self.__start_cgfs)

        wrapper = QWidget()
        self.__fields = fields
        self.__form_wrapper = wrapper

        res = QVBoxLayout(wrapper)

        if cgfs.newer_version_available():
            version_label = QLabel(
                'A new version of CodeGra.fs is available.\nYou can download'
                ' it at <a href="https://codegra.de/codegra_fs/latest"'
                ' >https://codegra.de/codegra_fs/latest/</a>'
            )
            version_label.setTextFormat(Qt.RichText)
            version_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
            version_label.setTextInteractionFlags(Qt.TextBrowserInteraction)
            version_label.setOpenExternalLinks(True)
            version_label.setStyleSheet("border: 1px solid gray; padding: 5px;")
            res.addWidget(version_label)
            res.addItem(
                QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Minimum)
            )

        res.addLayout(form)
        res.addWidget(self.__errs_field)
        res.addWidget(start_button)

        return wrapper


def main() -> None:
    global PREVIOUS_VALUES_PATH

    appdir = AppDirs('CodeGra_fs', 'CodeGrade')
    PREVIOUS_VALUES_PATH = os.path.join(
        appdir.user_data_dir, 'prev_values.json'
    )

    if not os.path.isdir(appdir.user_data_dir):
        os.makedirs(appdir.user_data_dir, exist_ok=True)

    app = QApplication(sys.argv)
    window = CGFSUi()
    try:
        app.exec_()
    finally:
        window.stop_cgfs()


if __name__ == '__main__':
    main()
