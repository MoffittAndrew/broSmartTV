print("Importing settings screen...")

from globals import DISPLAY, GUI
from ui.gui import CustomQWidget, MAIN_WINDOW
from ui.tools.button import Button
from ui.wifi_overlay import WifiOverlay

from PyQt5.QtWidgets import QLabel, QVBoxLayout

from interface.wifi_interface import wifiInterface

class SettingsScreen(CustomQWidget):
    def __init__(self, navBarButton = None, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.__navBarButton = None
        self.__currentNetwork = None

        self.__heading = QLabel("Wifi")
        self.__heading.setStyleSheet("font-size: 44px; font-weight: bold;")

        self.__currentNetworkLabel = QLabel()
        self.__currentNetworkLabel.setWordWrap(True)
        self.__currentNetworkLabel.setStyleSheet("font-size: 24px;")

        self.__switchNetworkButton = Button(text="Switch network", callback=self.openWifiOverlay)
        self.__wifiOverlay = WifiOverlay(parent=self, onClose=self._onOverlayClosed)

        layout = QVBoxLayout()
        layout.setContentsMargins(80, 60, 80, 60)
        layout.setSpacing(30)
        layout.addWidget(self.__heading)
        layout.addWidget(self.__currentNetworkLabel)
        layout.addWidget(self.__switchNetworkButton)
        layout.addStretch(1)

        self.setFixedWidth(DISPLAY.WIDTH)
        self.setFixedHeight(DISPLAY.HEIGHT - GUI.NAVBAR.BUTTON_HEIGHT)
        self.setLayout(layout)
        
        self.setNavBarButton(navBarButton)
        self.refreshCurrentNetwork()
        
    ## Getters
    
    def getNavBarButton(self):
        return self.__navBarButton
    
    def getPrimaryButton(self):
        if self.__wifiOverlay.isOverlayVisible():
            return self.__wifiOverlay.getPrimaryButton()
        return self.__switchNetworkButton

    def getCurrentNetwork(self):
        return self.__currentNetwork

    def _formatCurrentNetworkText(self, network):
        if network is None:
            return "Current network: not connected"

        known_networks = {known_network.ssid: known_network for known_network in wifiInterface.getKnownNetworks()}
        saved_text = "yes" if network.ssid in known_networks else "no"
        signal_text = f"{network.signal_strength}%" if network.signal_strength else "unknown"
        security_text = network.security if network.security else "unknown"

        return "\n".join([
            f"Current network: {network.ssid}",
            f"Signal strength: {signal_text}",
            f"Security: {security_text}",
            f"Saved network: {saved_text}",
        ])

    def refreshCurrentNetwork(self):
        try:
            self.__currentNetwork = wifiInterface.getCurrentNetwork()
            self.__currentNetworkLabel.setText(self._formatCurrentNetworkText(self.__currentNetwork))
        except Exception:
            self.__currentNetwork = None
            self.__currentNetworkLabel.setText("Current network: unavailable")
    
    def setNavBarButton(self, navBarButton):
        self.__navBarButton = navBarButton
        if navBarButton is not None:
            self.__switchNetworkButton.setNavUp(navBarButton)

    async def openWifiOverlay(self):
        await self.__wifiOverlay.showOverlay(navBarButton=self.getNavBarButton())
        inputInterface = MAIN_WINDOW.getInputInterface()
        if inputInterface is not None:
            inputInterface.setSelectedButton(self.getPrimaryButton())

    def _onOverlayClosed(self):
        inputInterface = MAIN_WINDOW.getInputInterface()
        if inputInterface is not None:
            inputInterface.setSelectedButton(self.getPrimaryButton())

    def showEvent(self, a0):
        self.__wifiOverlay.hide()
        self.refreshCurrentNetwork()
        return super().showEvent(a0)

    def resizeEvent(self, a0):
        super().resizeEvent(a0)
        self.__wifiOverlay.setGeometry(0, 0, self.width(), self.height())

settingsScreen = SettingsScreen()