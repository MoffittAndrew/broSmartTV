print("Importing wifi overlay...")

from globals import DISPLAY
from interface.wifi_interface import wifiInterface
from ui.gui import CustomQWidget
from ui.tools.button import Button

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QLabel, QScrollArea, QVBoxLayout, QWidget


class WifiOverlay(CustomQWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.__returnWidget = None
        self.__networkButtons = []
        self.__primaryButton = None

        self.__titleLabel = QLabel("Wifi networks")
        self.__titleLabel.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.__titleLabel.setStyleSheet("font-size: 48px; font-weight: bold;")

        self.__closeButton = Button(text="Back", callback=self.hideOverlay)

        self.__scrollArea = QScrollArea()
        self.__scrollArea.setWidgetResizable(True)
        self.__scrollArea.setFrameShape(QScrollArea.NoFrame)

        self.__contentWidget = QWidget()
        self.__contentLayout = QVBoxLayout(self.__contentWidget)
        self.__contentLayout.setContentsMargins(0, 0, 0, 0)
        self.__contentLayout.setSpacing(28)
        self.__scrollArea.setWidget(self.__contentWidget)

        layout = QVBoxLayout()
        layout.setContentsMargins(80, 60, 80, 60)
        layout.setSpacing(30)
        layout.addWidget(self.__titleLabel)
        layout.addWidget(self.__closeButton)
        layout.addWidget(self.__scrollArea)

        self.setFixedWidth(DISPLAY.WIDTH)
        self.setFixedHeight(DISPLAY.HEIGHT)
        self.setLayout(layout)

        self.refreshNetworks()

    def getPrimaryButton(self):
        if self.__primaryButton is not None:
            return self.__primaryButton
        return self.__closeButton

    def _makeSectionLabel(self, text):
        label = QLabel(text)
        label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        label.setStyleSheet("font-size: 32px; font-weight: bold;")
        return label

    def _makeNetworkButton(self, network):
        signal_text = f"{network.signal_strength}%" if network.signal_strength else "unknown signal"
        security_text = network.security if network.security else "unknown security"
        label = f"{network.ssid}\n{signal_text}  |  {security_text}"
        return Button(width=DISPLAY.WIDTH - 180, height=120, text=label)

    def _knownNetworkMap(self):
        return {network.ssid: network for network in wifiInterface.getKnownNetworks()}

    def refreshNetworks(self):
        while self.__contentLayout.count():
            item = self.__contentLayout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

        self.__networkButtons = []
        self.__primaryButton = None

        known_networks = self._knownNetworkMap()
        try:
            available_networks = wifiInterface.getAvailableNetworks()
        except Exception:
            available_networks = []

        known_available_networks = [network for network in available_networks if network.ssid in known_networks]
        other_available_networks = [network for network in available_networks if network.ssid not in known_networks]

        if known_available_networks:
            self.__contentLayout.addWidget(self._makeSectionLabel("Known networks"))
            for network in known_available_networks:
                button = self._makeNetworkButton(network)
                self.__networkButtons.append(button)
                self.__contentLayout.addWidget(button)

        if other_available_networks:
            self.__contentLayout.addWidget(self._makeSectionLabel("Available networks"))
            for network in other_available_networks:
                button = self._makeNetworkButton(network)
                self.__networkButtons.append(button)
                self.__contentLayout.addWidget(button)

        if not self.__networkButtons:
            empty_label = QLabel("No available networks found.")
            empty_label.setStyleSheet("font-size: 24px;")
            self.__contentLayout.addWidget(empty_label)
            self.__primaryButton = self.__closeButton
        else:
            self.__primaryButton = self.__networkButtons[0]
            self.__closeButton.setNavDown(self.__primaryButton)
            self.__primaryButton.setNavUp(self.__closeButton)

            for previous_button, next_button in zip(self.__networkButtons, self.__networkButtons[1:]):
                previous_button.setNavDown(next_button)
                next_button.setNavUp(previous_button)

        self.__contentLayout.addStretch(1)

    async def showOverlay(self, returnWidget=None):
        self.__returnWidget = returnWidget
        self.refreshNetworks()
        parent = self.parent()
        if parent is not None:
            parent.setTab(self)
        else:
            self.show()

    async def hideOverlay(self):
        parent = self.parent()
        if parent is not None and self.__returnWidget is not None:
            parent.setTab(self.__returnWidget)
        else:
            self.hide()
        self.__returnWidget = None


wifiOverlay = WifiOverlay()