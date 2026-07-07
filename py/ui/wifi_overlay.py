print("Importing wifi overlay...")

from globals import DISPLAY
from interface.wifi_interface import wifiInterface
from ui.gui import CustomQWidget
from ui.tools.button import Button

from PyQt5.QtWidgets import QLabel, QScrollArea, QVBoxLayout, QWidget


class WifiOverlay(CustomQWidget):
    def __init__(self, onClose=None, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.__onClose = onClose
        self.__networkButtons = []
        self.__primaryButton = None

        self.__titleLabel = QLabel("Wifi networks")
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
        self.setStyleSheet("background-color: rgba(0, 0, 0, 235);")
        self.hide()

        self.refreshNetworks()

    def getPrimaryButton(self):
        if self.__primaryButton is not None:
            return self.__primaryButton
        return self.__closeButton

    def isOverlayVisible(self):
        return self.isVisible()

    def _makeSectionLabel(self, text):
        label = QLabel(text)
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
        while self.__contentLayout.count() > 0:
            item = self.__contentLayout.takeAt(0)
            if item is None:
                continue
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

    async def showOverlay(self, navBarButton=None):
        self.refreshNetworks()
        self.__closeButton.setNavUp(navBarButton)
        self.show()
        self.raise_()

    async def hideOverlay(self):
        self.hide()
        if self.__onClose is not None:
            self.__onClose()