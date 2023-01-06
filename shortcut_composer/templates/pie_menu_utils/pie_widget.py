from typing import List

from PyQt5.QtCore import Qt, QPoint
from PyQt5.QtWidgets import QWidget
from PyQt5.QtGui import QColor, QPaintEvent

from api_krita.pyqt import Painter
from .pie_style import PieStyle
from .label_holder import LabelHolder
from .label_painter import LabelPainter, create_painter


class PieWidget(QWidget):
    def __init__(
        self,
        labels: LabelHolder,
        style: PieStyle,
        parent=None
    ):
        QWidget.__init__(self, parent)
        self.labels = labels
        self._style = style
        self._label_painters = self._create_label_painters()

        self.setWindowFlags(
            self.windowFlags() |
            Qt.Window |  # type: ignore
            Qt.FramelessWindowHint
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setStyleSheet("background: transparent;")
        self.setWindowTitle("Pie Menu")

        size = self._style.widget_radius*2
        self.setGeometry(0, 0, size, size)

    @property
    def center(self) -> QPoint:
        return QPoint(self._style.widget_radius, self._style.widget_radius)

    @property
    def center_global(self) -> QPoint:
        return self.pos() + self.center  # type: ignore

    @property
    def deadzone(self) -> float:
        """Return the deadzone distance."""
        return self._style.deadzone_radius

    @property
    def _no_border_radius(self) -> int:
        """Return radius of widget excluding width of border."""
        return self._style.pie_radius - self._style.border_thickness//2

    def move_center(self, new_center: QPoint) -> None:
        """Move the widget by providing a new center point."""
        self.move(new_center-self.center)  # type: ignore

    def paintEvent(self, event: QPaintEvent) -> None:
        with Painter(self, event) as painter:
            self._paint_deadzone_indicator(painter)
            self._paint_base_wheel(painter)
            self._paint_active_pie(painter)
            self._paint_base_border(painter)

            for label_painter in self._label_painters:
                label_painter.paint(painter)

    def _paint_base_wheel(self, painter: Painter) -> None:
        painter.paint_wheel(
            center=self.center,
            outer_radius=self._outer_radius,
            color=self._style.background_color,
            thickness=self._style.area_thickness,
        )

    def _paint_base_border(self, painter: Painter) -> None:
        painter.paint_wheel(
            center=self.center,
            outer_radius=self._style.pie_radius - self._style.area_thickness,
            color=self._style.border_color,
            thickness=self._style.border_thickness,
        )

    def _paint_deadzone_indicator(self, painter: Painter) -> None:
        if self.deadzone == float("inf"):
            return

        painter.paint_wheel(
            center=self.center,
            outer_radius=self.deadzone,
            color=QColor(128, 255, 128, 120),
            thickness=1,
        )
        painter.paint_wheel(
            center=self.center,
            outer_radius=self.deadzone-1,
            color=QColor(255, 128, 128, 120),
            thickness=1,
        )

    def _paint_active_pie(self, painter: Painter) -> None:
        if not self.labels.active:
            return

        painter.paint_pie(
            center=self.center,
            outer_radius=self._outer_radius,
            angle=self.labels.active.angle,
            span=360//len(self._label_painters),
            color=self._style.active_color,
            thickness=self._style.area_thickness,
        )

    def _create_label_painters(self) -> List[LabelPainter]: return [
        create_painter(label, self._style, self) for label in self.labels
    ]
