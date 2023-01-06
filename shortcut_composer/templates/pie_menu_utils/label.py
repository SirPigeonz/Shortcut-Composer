from typing import Optional, Union, Any
from dataclasses import dataclass
from abc import ABC, abstractmethod

from PyQt5.QtCore import QPoint, Qt
from PyQt5.QtGui import QFont, QPixmap, QColor
from PyQt5.QtWidgets import QLabel, QWidget

from api_krita import pyqt
from api_krita.pyqt import Painter, Text
from .pie_style import PieStyle


@dataclass
class Label:

    value: Any
    center: QPoint = QPoint(0, 0)
    angle: int = 0
    display_value: Union[QPixmap, Text, None] = None

    @property
    def text(self) -> Optional[Text]:
        if isinstance(self.display_value, Text):
            return self.display_value

    @property
    def image(self) -> Optional[QPixmap]:
        if isinstance(self.display_value, QPixmap):
            return self.display_value

    def get_painter(self, widget: QWidget, style: PieStyle) -> 'LabelPainter':
        if self.image:
            return ImageLabelPainter(self, widget, style)
        elif self.text:
            return TextLabelPainter(self, widget, style)
        raise ValueError(f"Label {self} is not valid")


@dataclass
class LabelPainter(ABC):

    label: Label
    widget: QWidget
    style: PieStyle

    @abstractmethod
    def paint(self, painter: Painter) -> None: ...


@dataclass
class TextLabelPainter(LabelPainter):

    def __post_init__(self):
        self._pyqt_label = self._create_pyqt_label()

    def paint(self, painter: Painter):
        painter.paint_wheel(
            center=self.label.center,
            outer_radius=self.style.icon_radius,
            color=self.style.icon_color,
        )
        painter.paint_wheel(
            center=self.label.center,
            outer_radius=self.style.icon_radius,
            color=self.style.border_color,
            thickness=self.style.border_thickness,
        )

    def _create_pyqt_label(self) -> QLabel:
        if not isinstance(self.label.text, Text):
            raise TypeError("Label supposed to be text.")

        font_size = round(self.style.icon_radius*0.45)
        heigth = round(self.style.icon_radius*0.8)

        label = QLabel(self.widget)
        label.setText(self.label.text.value)
        label.setFont(QFont('Helvetica', font_size, QFont.Bold))
        label.setAlignment(Qt.AlignCenter)
        label.setGeometry(0, 0, round(heigth*2), round(heigth))
        label.move(self.label.center.x()-heigth,
                   self.label.center.y()-heigth//2)
        label.setStyleSheet(f'''
            background-color:rgba({self._color_to_str(self.style.icon_color)});
            color:rgba({self._color_to_str(self.label.text.color)});
        ''')

        label.show()
        return label

    @staticmethod
    def _color_to_str(color: QColor) -> str: return f'''
        {color.red()}, {color.green()}, {color.blue()}, {color.alpha()}'''


@dataclass
class ImageLabelPainter(LabelPainter):
    def __post_init__(self):
        self.ready_image = self._prepare_image()

    def paint(self, painter: Painter):
        painter.paint_wheel(
            center=self.label.center,
            outer_radius=self.style.icon_radius,
            color=self.style.icon_color
        )
        painter.paint_wheel(
            center=self.label.center,
            outer_radius=self.style.icon_radius-self.style.border_thickness//2,
            color=self.style.border_color,
            thickness=self.style.border_thickness,
        )
        painter.paint_pixmap(self.label.center, self.ready_image)

    def _prepare_image(self):
        if not isinstance(self.label.image, QPixmap):
            raise TypeError("Label supposed to be pixmap.")

        rounded_image = pyqt.make_pixmap_round(self.label.image)
        return pyqt.scale_pixmap(
            pixmap=rounded_image,
            size_px=round(self.style.icon_radius*1.8)
        )
