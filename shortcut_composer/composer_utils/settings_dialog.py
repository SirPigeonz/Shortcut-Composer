# SPDX-FileCopyrightText: © 2022 Wojciech Trybus <wojtryb@gmail.com>
# SPDX-License-Identifier: GPL-3.0-or-later

from typing import Set, Optional

from PyQt5.QtWidgets import (
    QAbstractItemView,
    QVBoxLayout,
    QListWidget,
    QPushButton,
    QHBoxLayout,
    QTabWidget,
    QComboBox,
    QWidget,
    QDialog,
)
from PyQt5.QtCore import QSize
from PyQt5.QtGui import QCursor

from api_krita import Krita
from api_krita.enums import BlendingMode, Tool
from .config import Config
from .settings_dialog_utils import (
    ComboBoxesLayout,
    SpinBoxesLayout,
    ButtonsLayout
)


class SettingsDialog(QDialog):
    """Dialog which allows to change global settings of the plugin."""

    def __init__(self) -> None:
        super().__init__()

        self.setMinimumSize(QSize(300, 200))
        self.setWindowTitle("Configure Shortcut Composer")

        self._tab_dict = {
            "General": GeneralSettingsTab(),
            "Pie values": PieValuesTab(),
        }
        tab_holder = QTabWidget()
        for name, tab in self._tab_dict.items():
            tab_holder.addTab(tab, name)

        full_layout = QVBoxLayout(self)
        full_layout.addWidget(tab_holder)
        full_layout.addLayout(ButtonsLayout(
            ok_callback=self.ok,
            apply_callback=self.apply,
            reset_callback=self.reset,
            cancel_callback=self.hide,
        ))
        self.setLayout(full_layout)

    def show(self) -> None:
        """Show the dialog after refreshing all its elements."""
        self.refresh()
        self.move(QCursor.pos())
        return super().show()

    def apply(self) -> None:
        """Ask all dialog zones to apply themselves."""
        for tab in self._tab_dict.values():
            tab.apply()
        Krita.trigger_action("Reload Shortcut Composer")

    def ok(self) -> None:
        """Hide the dialog after applying the changes"""
        self.apply()
        self.hide()

    def reset(self) -> None:
        """Reset all config values to defaults in krita and elements."""
        Config.reset_defaults()
        self.refresh()

    def refresh(self):
        """Ask all tabs to refresh themselves. """
        for tab in self._tab_dict.values():
            tab.refresh()


class GeneralSettingsTab(QWidget):
    """Dialog which allows to change global settings of the plugin."""

    def __init__(self) -> None:
        super().__init__()

        self._layouts_dict = {
            "ComboBoxes": ComboBoxesLayout(),
            "SpinBoxes": SpinBoxesLayout(),
        }
        full_layout = QVBoxLayout()
        for layout in self._layouts_dict.values():
            full_layout.addLayout(layout)
        self.setLayout(full_layout)

    def apply(self) -> None:
        """Ask all dialog zones to apply themselves."""
        for layout in self._layouts_dict.values():
            layout.apply()

    def refresh(self) -> None:
        """Ask all dialog zones to refresh themselves. """
        for layout in self._layouts_dict.values():
            layout.refresh()


class PieValuesTab(QWidget):
    def __init__(self) -> None:
        super().__init__()
        layout = QVBoxLayout()
        self.combo_widget_picker = QComboBox()
        self.widgets = {
            "Blending modes": PieValues(
                allowed_values=set(BlendingMode._member_names_),
                config=Config.BLENDING_MODES_VALUES
            ),
            "Selection tools": PieValues(
                allowed_values=set(Tool._member_names_),
                config=Config.SELECTION_TOOLS_VALUES
            ),
            "Misc tools": PieValues(
                allowed_values=set(Tool._member_names_),
                config=Config.MISC_TOOLS_VALUES
            ),
            "Transform modes": PieValues(
                allowed_values=set(Tool._member_names_),
                config=Config.TRANSFORM_MODES_VALUES
            ),
        }
        self.combo_widget_picker.addItems(self.widgets.keys())
        self.combo_widget_picker.currentTextChanged.connect(
            self._change_widget)

        layout.addWidget(self.combo_widget_picker)
        for widget in self.widgets.values():
            widget.hide()
            layout.addWidget(widget)
        self.widgets["Blending modes"].show()
        self.setLayout(layout)

    def _change_widget(self):
        for widget in self.widgets.values():
            widget.hide()
        self.widgets[self.combo_widget_picker.currentText()].show()

    def apply(self) -> None:
        """Ask all dialog zones to apply themselves."""
        for widget in self.widgets.values():
            widget.apply()

    def refresh(self) -> None:
        """Ask all dialog zones to refresh themselves."""
        for widget in self.widgets.values():
            widget.refresh()


class PieValues(QWidget):
    def __init__(self, allowed_values: Set[str], config: Config) -> None:
        super().__init__()
        layout = QVBoxLayout()
        self.allowed_values = sorted(allowed_values)
        self.config = config

        self.list_widget = ValueList(self)

        self.combo_box = QComboBox()
        self.combo_box.addItems(self.allowed_values)

        add_button = QPushButton(Krita.get_icon("list-add"), "")
        add_button.setFixedWidth(40)
        add_button.clicked.connect(self.add)

        remove_button = QPushButton(Krita.get_icon("deletelayer"), "")
        remove_button.setFixedWidth(40)
        remove_button.clicked.connect(self.list_widget.remove_selected)

        control_layout = QHBoxLayout()
        control_layout.addWidget(self.combo_box)
        control_layout.addWidget(add_button)
        control_layout.addWidget(remove_button)

        layout.addLayout(control_layout)
        layout.addWidget(self.list_widget)

        self.setLayout(layout)

    def add(self):
        self.list_widget.insert(
            position=self.list_widget.current_row,
            value=self.combo_box.currentText()
        )

    def apply(self):
        texts = []
        for row in range(self.list_widget.count()):
            texts.append(self.list_widget.item(row).text())
        self.config.write(";".join(texts))

    def refresh(self):
        self.list_widget.clear()
        currently_set: str = self.config.read()
        self.list_widget.addItems(currently_set.split(";"))


class ValueList(QListWidget):
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setDragDropMode(QAbstractItemView.InternalMove)
        self.setSelectionMode(QAbstractItemView.ExtendedSelection)

    @property
    def current_row(self):
        if not self.selectedIndexes():
            return self.count()
        return self.currentRow()

    def insert(self, position: int, value: str):
        self.insertItem(position+1, value)
        self.clearSelection()
        self.setCurrentRow(position+1)

    def remove_selected(self):
        selected = self.selectedIndexes()
        indices = [item.row() for item in selected]
        for index in sorted(indices, reverse=True):
            self.takeItem(index)

        if selected:
            first_deleted_row = min([item.row() for item in selected])
            self.clearSelection()
            self.setCurrentRow(first_deleted_row-1)
