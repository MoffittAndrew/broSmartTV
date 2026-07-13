print("Importing custom gui section classes...")

from globals import GUI
from ui.gui import CustomQWidget

from PyQt5.QtWidgets import QVBoxLayout, QHBoxLayout, QGridLayout
from PyQt5.QtCore import Qt

class BaseSection(CustomQWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._widgets = []
        self._horizontalSpacing = GUI.SPACING.NORMAL
        self._verticalSpacing = GUI.SPACING.NORMAL
        self._margins = (0, 0, 0, 0)
        self._layout = None

    def _clearLayout(self):
        if self._layout is None:
            return

        while self._layout.count() > 0:
            item = self._layout.takeAt(0)
            childLayout = item.layout()
            if childLayout is not None:
                while childLayout.count() > 0:
                    childLayout.takeAt(0)

    def _applyLayoutConfig(self):
        if self._layout is None:
            return

        left, top, right, bottom = self._margins
        self._layout.setContentsMargins(left, top, right, bottom)

    def setSpacing(self, spacing):
        spacing = max(0, int(spacing))
        self._horizontalSpacing = spacing
        self._verticalSpacing = spacing
        if self._layout is not None and hasattr(self._layout, "setSpacing"):
            self._layout.setSpacing(spacing)

    def setHorizontalSpacing(self, spacing):
        self._horizontalSpacing = max(0, int(spacing))
        if self._layout is not None and hasattr(self._layout, "setHorizontalSpacing"):
            self._layout.setHorizontalSpacing(self._horizontalSpacing)
        elif self._layout is not None and hasattr(self._layout, "setSpacing"):
            self._layout.setSpacing(self._horizontalSpacing)

    def setVerticalSpacing(self, spacing):
        self._verticalSpacing = max(0, int(spacing))
        if self._layout is not None and hasattr(self._layout, "setVerticalSpacing"):
            self._layout.setVerticalSpacing(self._verticalSpacing)
        elif self._layout is not None and hasattr(self._layout, "setSpacing"):
            self._layout.setSpacing(self._verticalSpacing)

    def getHorizontalSpacing(self):
        return self._horizontalSpacing

    def getVerticalSpacing(self):
        return self._verticalSpacing

    def setMargins(self, left=0, top=0, right=0, bottom=0):
        self._margins = (int(left), int(top), int(right), int(bottom))
        self._applyLayoutConfig()

    def getMargins(self):
        return self._margins

    def setWidgets(self, widgets):
        self._widgets = list(widgets)

    def getWidgets(self):
        return self._widgets

    def getButtons(self):
        return self.getWidgets()

    def setButtons(self, buttons):
        self.setWidgets(buttons)

    def _isNavigable(self, widget):
        return all(
            hasattr(widget, method)
            for method in ["setNavUp", "setNavRight", "setNavDown", "setNavLeft"]
        )

    def _wireVerticalNavigation(self, widgets):
        navigable = [widget for widget in widgets if self._isNavigable(widget)]
        for index in range(len(navigable) - 1):
            upper = navigable[index]
            lower = navigable[index + 1]
            upper.setNavDown(lower)
            lower.setNavUp(upper)

    def _wireHorizontalNavigation(self, widgets):
        navigable = [widget for widget in widgets if self._isNavigable(widget)]
        for index in range(len(navigable) - 1):
            leftWidget = navigable[index]
            rightWidget = navigable[index + 1]
            leftWidget.setNavRight(rightWidget)
            rightWidget.setNavLeft(leftWidget)

    def _measureWidth(self):
        max_width = 0
        for widget in self.getWidgets():
            max_width = max(max_width, widget.width())
        return max_width

    def _measureHeight(self):
        total_height = 0
        for widget in self.getWidgets():
            total_height += widget.height()
        return total_height


class VSection(BaseSection):
    def __init__(self, widgets=None, spacing=GUI.SPACING.NORMAL, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setSpacing(spacing)
        self._layout = QVBoxLayout()
        self._layout.setSpacing(self.getVerticalSpacing())
        self.setLayout(self._layout)
        self.setWidgets(widgets or [])

    def setWidgets(self, widgets):
        super().setWidgets(widgets)
        self._clearLayout()
        self._layout.setSpacing(self.getVerticalSpacing())
        self._applyLayoutConfig()

        for widget in self.getWidgets():
            self._layout.addWidget(widget)

        self._wireVerticalNavigation(self.getWidgets())

        left, _, right, _ = self.getMargins()
        width = self._measureWidth() + left + right
        if len(self.getWidgets()) == 0:
            height = 0
        else:
            spacing = (len(self.getWidgets()) - 1) * self.getVerticalSpacing()
            _, top, _, bottom = self.getMargins()
            height = self._measureHeight() + spacing + top + bottom

        self.setFixedWidth(width)
        self.setFixedHeight(height)


class HSection(BaseSection):
    def __init__(self, widgets=None, spacing=GUI.SPACING.NORMAL, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setSpacing(spacing)
        self._layout = QHBoxLayout()
        self._layout.setSpacing(self.getHorizontalSpacing())
        self.setLayout(self._layout)
        self.setWidgets(widgets or [])

    def setWidgets(self, widgets):
        super().setWidgets(widgets)
        self._clearLayout()
        self._layout.setSpacing(self.getHorizontalSpacing())
        self._applyLayoutConfig()

        for widget in self.getWidgets():
            self._layout.addWidget(widget)

        self._wireHorizontalNavigation(self.getWidgets())

        top = self.getMargins()[1]
        bottom = self.getMargins()[3]
        height = max(0, self._measureHeight()) + top + bottom

        left = self.getMargins()[0]
        right = self.getMargins()[2]
        if len(self.getWidgets()) == 0:
            width = left + right
        else:
            spacing = (len(self.getWidgets()) - 1) * self.getHorizontalSpacing()
            total_width = 0
            for widget in self.getWidgets():
                total_width += widget.width()
            width = total_width + spacing + left + right

        self.setFixedWidth(width)
        self.setFixedHeight(height)


class GridSection(BaseSection):
    def __init__(self, columns=1, widgets=None, spacing=GUI.SPACING.TIGHT, edgePolicy="last", *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._layout = QGridLayout()
        self._layout.setOriginCorner(Qt.TopLeftCorner)
        self.setLayout(self._layout)
        self._columns = 1
        self._rows = []
        self._edgePolicy = edgePolicy
        self.setSpacing(spacing)
        self.setColumns(columns)
        self.setWidgets(widgets or [])

    def setColumns(self, columns):
        self._columns = max(1, int(columns))

    def getColumns(self):
        return self._columns

    def getRows(self):
        return self._rows

    def _buildRows(self):
        rows = []
        currentRow = []
        for widget in self.getWidgets():
            currentRow.append(widget)
            if len(currentRow) == self.getColumns():
                rows.append(currentRow)
                currentRow = []

        if len(currentRow) > 0:
            rows.append(currentRow)

        self._rows = rows

    def _wireGridNavigation(self):
        rows = self.getRows()
        for row in rows:
            self._wireHorizontalNavigation(row)

        if len(rows) == 0:
            return

        for rowIndex in range(len(rows) - 1):
            upperRow = rows[rowIndex]
            lowerRow = rows[rowIndex + 1]

            for columnIndex in range(len(upperRow)):
                upperWidget = upperRow[columnIndex]
                if not self._isNavigable(upperWidget):
                    continue

                if columnIndex < len(lowerRow):
                    lowerWidget = lowerRow[columnIndex]
                elif self._edgePolicy == "last" and len(lowerRow) > 0:
                    lowerWidget = lowerRow[-1]
                else:
                    continue

                if not self._isNavigable(lowerWidget):
                    continue

                upperWidget.setNavDown(lowerWidget)
                lowerWidget.setNavUp(upperWidget)

    def setWidgets(self, widgets):
        super().setWidgets(widgets)
        self._clearLayout()
        self._layout.setHorizontalSpacing(self.getHorizontalSpacing())
        self._layout.setVerticalSpacing(self.getVerticalSpacing())
        self._applyLayoutConfig()
        self._buildRows()

        rows = self.getRows()
        for rowIndex in range(len(rows)):
            for columnIndex in range(len(rows[rowIndex])):
                self._layout.addWidget(rows[rowIndex][columnIndex], rowIndex, columnIndex)

        self._wireGridNavigation()

        rowHeights = []
        for row in rows:
            maxHeight = 0
            for widget in row:
                maxHeight = max(maxHeight, widget.height())
            rowHeights.append(maxHeight)

        columnWidths = [0] * self.getColumns()
        for row in rows:
            for columnIndex, widget in enumerate(row):
                columnWidths[columnIndex] = max(columnWidths[columnIndex], widget.width())

        left, top, right, bottom = self.getMargins()
        usedColumns = [width for width in columnWidths if width > 0]
        usedRows = [height for height in rowHeights if height > 0]

        width = left + right + sum(usedColumns)
        height = top + bottom + sum(usedRows)

        if len(usedColumns) > 1:
            width += (len(usedColumns) - 1) * self.getHorizontalSpacing()

        if len(usedRows) > 1:
            height += (len(usedRows) - 1) * self.getVerticalSpacing()

        self.setFixedWidth(width)
        self.setFixedHeight(height)

    def getPrimaryButton(self):
        rows = self.getRows()
        if len(rows) == 0 or len(rows[0]) == 0:
            return None
        return rows[0][0]
