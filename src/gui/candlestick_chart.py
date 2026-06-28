from __future__ import annotations

from typing import Sequence

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import QWidget


CHART_VISIBLE_ROWS = 120
PRICE_AXIS_WIDTH = 64
ENABLED_EMA_PERIODS = [20, 50, 200]
EMA_COLORS = {
    20: QColor("#f4c542"),
    50: QColor("#4aa3ff"),
    200: QColor("#c77dff"),
}


class CandlestickChart(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self._rows: list[dict[str, object]] = []
        self.setMinimumHeight(360)

    def set_ohlc_data(self, rows: Sequence[dict[str, object]]) -> None:
        self._rows = list(rows)[-CHART_VISIBLE_ROWS:]
        self.update()

    def rendered_rows(self) -> list[dict[str, object]]:
        return list(self._rows)

    def clear(self) -> None:
        self._rows = []
        self.update()

    def paintEvent(self, event) -> None:  # noqa: N802
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.fillRect(self.rect(), QColor("#101418"))

        price_rect, volume_rect = self._chart_rects()
        self._draw_frame(painter, price_rect)
        self._draw_frame(painter, volume_rect)

        if not self._rows:
            self._draw_empty_state(painter, price_rect)
            return

        self._draw_candles(painter, price_rect, volume_rect)

    def _chart_rects(self) -> tuple[QRectF, QRectF]:
        margin_left = 16
        margin_top = 24
        margin_right = 24 + PRICE_AXIS_WIDTH
        margin_bottom = 34
        available_height = max(10, self.height() - margin_top - margin_bottom)
        gap = 12
        volume_height = max(54, available_height * 0.22)
        price_height = max(10, available_height - volume_height - gap)
        chart_width = max(10, self.width() - margin_left - margin_right)
        price_rect = QRectF(
            margin_left,
            margin_top,
            chart_width,
            price_height,
        )
        volume_rect = QRectF(
            margin_left,
            price_rect.bottom() + gap,
            chart_width,
            volume_height,
        )
        return price_rect, volume_rect

    def _draw_frame(self, painter: QPainter, chart_rect: QRectF) -> None:
        grid_pen = QPen(QColor("#26313a"))
        painter.setPen(grid_pen)
        painter.drawRect(chart_rect)

        for index in range(1, 4):
            y = chart_rect.top() + chart_rect.height() * index / 4
            painter.drawLine(QPointF(chart_rect.left(), y), QPointF(chart_rect.right(), y))

    def _draw_empty_state(self, painter: QPainter, chart_rect: QRectF) -> None:
        painter.setPen(QColor("#b8c2cc"))
        painter.drawText(chart_rect, Qt.AlignCenter, "No OHLC data available")

    def _draw_candles(
        self, painter: QPainter, price_rect: QRectF, volume_rect: QRectF
    ) -> None:
        values = []
        for row in self._rows:
            values.extend(
                [
                    float(row["high"]),
                    float(row["low"]),
                    float(row["open"]),
                    float(row["close"]),
                ]
            )

        low_price = min(values)
        high_price = max(values)
        price_range = high_price - low_price or 1.0
        candle_count = len(self._rows)
        slot_width = price_rect.width() / candle_count
        candle_width = max(3.0, min(14.0, slot_width * 0.58))
        max_volume = max(int(row["volume"]) for row in self._rows) or 1

        for index, row in enumerate(self._rows):
            open_price = float(row["open"])
            high = float(row["high"])
            low = float(row["low"])
            close = float(row["close"])
            volume = int(row["volume"])
            x = price_rect.left() + slot_width * index + slot_width / 2

            y_high = self._price_to_y(high, low_price, price_range, price_rect)
            y_low = self._price_to_y(low, low_price, price_range, price_rect)
            y_open = self._price_to_y(open_price, low_price, price_range, price_rect)
            y_close = self._price_to_y(close, low_price, price_range, price_rect)

            up_color = QColor("#2ecc71")
            down_color = QColor("#e05a47")
            candle_color = up_color if close >= open_price else down_color
            painter.setPen(QPen(candle_color, 1.2))
            painter.drawLine(QPointF(x, y_high), QPointF(x, y_low))

            body_top = min(y_open, y_close)
            body_height = max(2.0, abs(y_close - y_open))
            body_rect = QRectF(
                x - candle_width / 2,
                body_top,
                candle_width,
                body_height,
            )
            painter.fillRect(body_rect, candle_color)
            painter.drawRect(body_rect)

            volume_height = (volume / max_volume) * volume_rect.height()
            volume_rect_bar = QRectF(
                x - candle_width / 2,
                volume_rect.bottom() - volume_height,
                candle_width,
                max(1.0, volume_height),
            )
            painter.fillRect(volume_rect_bar, candle_color)

        self._draw_ema_overlays(painter, price_rect, low_price, price_range, slot_width)
        self._draw_ema_legend(painter, price_rect)
        painter.setPen(QColor("#b8c2cc"))
        self._draw_axis_label(painter, price_rect, price_rect.top(), f"{high_price:.2f}")
        self._draw_axis_label(painter, price_rect, price_rect.bottom(), f"{low_price:.2f}")
        self._draw_axis_label(
            painter, volume_rect, volume_rect.top(), self._format_volume(max_volume)
        )
        self._draw_axis_label(painter, volume_rect, volume_rect.bottom(), "0")
        self._draw_current_price_line(painter, price_rect, low_price, price_range)

    def _draw_axis_label(
        self, painter: QPainter, chart_rect: QRectF, y_position: float, text: str
    ) -> None:
        label_rect = QRectF(
            chart_rect.right() + 4,
            self._bounded_label_y(y_position, 16, chart_rect),
            PRICE_AXIS_WIDTH - 8,
            16,
        )
        painter.setPen(QColor("#b8c2cc"))
        painter.drawText(label_rect, Qt.AlignVCenter | Qt.AlignLeft, text)

    def _draw_ema_overlays(
        self,
        painter: QPainter,
        price_rect: QRectF,
        low_price: float,
        price_range: float,
        slot_width: float,
    ) -> None:
        for period in ENABLED_EMA_PERIODS:
            ema_values = self._calculate_ema_values(period)
            if len(ema_values) < 2:
                continue

            painter.setPen(QPen(self._ema_color(period), 1.4))
            previous_point: QPointF | None = None
            for row_index, ema_value in enumerate(ema_values):
                x = price_rect.left() + slot_width * row_index + slot_width / 2
                y = self._price_to_y(ema_value, low_price, price_range, price_rect)
                point = QPointF(x, y)
                if previous_point is not None:
                    painter.drawLine(previous_point, point)
                previous_point = point

    def _draw_ema_legend(self, painter: QPainter, price_rect: QRectF) -> None:
        x = price_rect.left() + 8
        y = price_rect.top() + 8
        for period in ENABLED_EMA_PERIODS:
            color = self._ema_color(period)
            painter.setPen(QPen(color, 1.4))
            painter.drawLine(QPointF(x, y + 7), QPointF(x + 18, y + 7))
            painter.setPen(color)
            painter.drawText(QRectF(x + 24, y, 58, 16), Qt.AlignVCenter, f"EMA{period}")
            x += 86

    def _ema_color(self, period: int) -> QColor:
        return EMA_COLORS.get(period, QColor("#f4c542"))

    def _calculate_ema_values(self, period: int) -> list[float]:
        closes = [float(row["close"]) for row in self._rows]
        if not closes:
            return []

        multiplier = 2 / (period + 1)
        ema_values = [closes[0]]
        for close in closes[1:]:
            ema_values.append((close - ema_values[-1]) * multiplier + ema_values[-1])
        return ema_values

    def _draw_current_price_line(
        self,
        painter: QPainter,
        price_rect: QRectF,
        low_price: float,
        price_range: float,
    ) -> None:
        latest_row = self._rows[-1]
        latest_open = float(latest_row["open"])
        latest_close = float(latest_row["close"])
        line_color = QColor("#2ecc71") if latest_close >= latest_open else QColor("#e05a47")
        y_close = self._price_to_y(latest_close, low_price, price_range, price_rect)

        line_pen = QPen(line_color, 1.1, Qt.DashLine)
        painter.setPen(line_pen)
        painter.drawLine(
            QPointF(price_rect.left(), y_close),
            QPointF(price_rect.right(), y_close),
        )

        label_text = f"{latest_close:.2f}"
        label_width = PRICE_AXIS_WIDTH - 8
        label_height = 18
        label_x = price_rect.right() + 4
        label_y = self._bounded_label_y(y_close, label_height, price_rect)
        label_rect = QRectF(
            label_x,
            label_y,
            label_width,
            label_height,
        )
        painter.fillRect(label_rect, QColor("#101418"))
        painter.setPen(QPen(line_color, 1.0))
        painter.drawRect(label_rect)
        painter.drawText(label_rect, Qt.AlignCenter, label_text)

    def _bounded_label_y(
        self, y_position: float, label_height: float, price_rect: QRectF
    ) -> float:
        return min(
            max(y_position - label_height / 2, price_rect.top()),
            price_rect.bottom() - label_height,
        )

    def _price_to_y(
        self, price: float, low_price: float, price_range: float, chart_rect: QRectF
    ) -> float:
        normalized = (price - low_price) / price_range
        return chart_rect.bottom() - normalized * chart_rect.height()

    def _format_volume(self, volume: int) -> str:
        if volume >= 1_000_000:
            return f"{volume / 1_000_000:.1f}M"
        if volume >= 1_000:
            return f"{volume / 1_000:.1f}K"
        return str(volume)
