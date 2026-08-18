print("Importing settings screen...")

from globals import DISPLAY, GUI
from ui.gui import CustomQWidget, MAIN_WINDOW
from ui.tools.button import Button
from ui.tools.menu_overlay import MenuOverlay
from ui.tools.section import VSection
from ui.wifi_overlay import WifiOverlay

from PyQt5.QtWidgets import QLabel, QVBoxLayout

from interface.git_interface import gitInterface
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

        self.__switchNetworkButton = Button(text="Switch network", clickCallback=self.openWifiOverlay)
        self.__wifiOverlay = WifiOverlay(parent=self, onClose=self._onOverlayClosed)

        self.__currentBranchLabel = QLabel()
        self.__currentBranchLabel.setWordWrap(True)
        self.__currentBranchLabel.setStyleSheet("font-size: 24px;")

        self.__switchBranchButton = Button(text="Switch git branch", clickCallback=self.openBranchMenu)
        self.__branchMenuOverlay = MenuOverlay(parent=self, onClose=self._onBranchMenuClosed)

        self.__contentSection = VSection(spacing=GUI.SPACING.WIDE)
        self.__contentSection.setMargins(*GUI.MARGINS.STANDARD)
        self.__contentSection.setWidgets([
            self.__heading,
            self.__currentNetworkLabel,
            self.__switchNetworkButton,
            self.__currentBranchLabel,
            self.__switchBranchButton,
        ])

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self.__contentSection)
        layout.addStretch(1)

        self.setFixedWidth(DISPLAY.WIDTH)
        self.setFixedHeight(DISPLAY.HEIGHT - GUI.NAVBAR.BUTTON_HEIGHT)
        self.setLayout(layout)
        
        self.setNavBarButton(navBarButton)
        self.refreshCurrentNetwork()
        self.refreshCurrentBranch()
        
    ## Getters
    
    def getNavBarButton(self):
        return self.__navBarButton
    
    def getPrimaryButton(self):
        if self.__wifiOverlay.isOverlayVisible():
            return self.__wifiOverlay.getPrimaryButton()
        if self.__branchMenuOverlay.isOverlayVisible():
            return self.__branchMenuOverlay.getPrimaryButton()
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

    def refreshCurrentBranch(self):
        try:
            self.__currentBranchLabel.setText(f"Current branch: {gitInterface.getCurrentBranch()}")
        except Exception:
            self.__currentBranchLabel.setText("Current branch: unavailable")
    
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

    async def openBranchMenu(self):
        message = ""
        try:
            branches = gitInterface.refreshAvailableBranches()
        except Exception as error:
            branches = []
            message = f"Could not refresh branches: {error}"

        options = [
            {"text": branch, "clickCallback": self._makeBranchSelectCallback(branch)}
            for branch in branches
        ]
        await self.__branchMenuOverlay.showOverlay(
            title="Switch git branch",
            message=message,
            options=options,
            navBarButton=self.getNavBarButton(),
        )

        inputInterface = MAIN_WINDOW.getInputInterface()
        if inputInterface is not None:
            inputInterface.setSelectedButton(self.getPrimaryButton())

    def _makeBranchSelectCallback(self, branch):
        async def onSelect():
            try:
                gitInterface.switchBranch(branch)
            except Exception:
                pass
            await self.__branchMenuOverlay.hideOverlay()
            self.refreshCurrentBranch()

        return onSelect

    def _onBranchMenuClosed(self):
        inputInterface = MAIN_WINDOW.getInputInterface()
        if inputInterface is not None:
            inputInterface.setSelectedButton(self.getPrimaryButton())

    def showEvent(self, a0):
        self.__wifiOverlay.hide()
        self.__branchMenuOverlay.hide()
        self.refreshCurrentNetwork()
        self.refreshCurrentBranch()
        return super().showEvent(a0)

    def resizeEvent(self, a0):
        super().resizeEvent(a0)
        self.__wifiOverlay.setGeometry(0, 0, self.width(), self.height())
        self.__branchMenuOverlay.setGeometry(0, 0, self.width(), self.height())

settingsScreen = SettingsScreen()