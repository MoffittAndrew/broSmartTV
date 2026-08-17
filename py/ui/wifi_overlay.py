print("Importing wifi overlay...")

import asyncio

from globals import DISPLAY, GUI
from interface.wifi_interface import wifiInterface
from ui.gui import CustomQWidget, MAIN_WINDOW
from ui.tools.button import Button
from ui.tools.section import VSection

from PyQt5.QtWidgets import QLabel, QScrollArea, QVBoxLayout, QWidget


class WifiOverlay(CustomQWidget):
    def __init__(self, onClose=None, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.__onClose = onClose
        self.__networkButtons = []
        self.__primaryButton = None
        self.__isConnecting = False
        self.__connectingNetwork = None

        self.__titleLabel = QLabel("Wifi networks")
        self.__titleLabel.setStyleSheet("font-size: 48px; font-weight: bold;")

        self.__statusLabel = QLabel("")
        self.__statusLabel.setWordWrap(True)
        self.__statusLabel.setStyleSheet("font-size: 24px;")

        self.__closeButton = Button(text="Back", clickCallback=self.hideOverlay)
        self.__refreshButton = Button(text="Refresh", clickCallback=self._onRefreshRequested)
        self.__controlsSection = VSection(
            widgets=[self.__closeButton, self.__refreshButton],
            spacing=GUI.SPACING.WIDE,
        )

        self.__scrollArea = QScrollArea()
        self.__scrollArea.setWidgetResizable(True)
        self.__scrollArea.setFrameShape(QScrollArea.NoFrame)
        self._resetContentContainer()

        layout = QVBoxLayout()
        layout.setContentsMargins(*GUI.MARGINS.STANDARD)
        layout.setSpacing(GUI.SPACING.WIDE)
        layout.addWidget(self.__titleLabel)
        layout.addWidget(self.__statusLabel)
        layout.addWidget(self.__controlsSection)
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
        status_text = ""
        if self.__connectingNetwork is not None and self.__connectingNetwork.ssid == network.ssid:
            if self.__isConnecting:
                status_text = "\n[connecting...]"
            else:
                status_text = "\n[connection failed]"
        elif network.is_current:
            status_text = "\n[connected]"
        label = f"{network.ssid}  |  Signal strength: {signal_text}  |  Security: {security_text}"
        label = f"{label}{status_text}"
        button = Button(width=DISPLAY.WIDTH - 180, height=120, text=label)
        button.setClickCallback(self._onNetworkSelected, network)
        return button

    async def _onNetworkSelected(self, network):
        known_network = None
        for saved_network in wifiInterface.getKnownNetworks():
            if saved_network.ssid == network.ssid:
                known_network = saved_network
                break

        if known_network is not None and known_network.password:
            network.password = known_network.password

        requiresPassword = network.requiresPassword
        if requiresPassword and not network.password:
            MAIN_WINDOW.openTextInput(
                prompt=f"Password for {network.ssid}",
                masked=True,
                maxLength=128,
                onSubmit=lambda password: self._queueConnection(network, password),
                onCancel=self._onKeyboardCancelled,
            )
            self.__statusLabel.setText(f"Enter password for {network.ssid}")
            return

        self._queueConnection(network, network.password)

    def _queueConnection(self, network, password):
        if self.__isConnecting:
            self.__statusLabel.setText("Already connecting. Please wait...")
            return

        network.password = password
        self.__connectingNetwork = network
        self.__isConnecting = True
        self.__statusLabel.setText(f"Connecting to {network.ssid}...")
        self.refreshNetworks()
        self._syncSelection()
        asyncio.create_task(self._connectToNetwork(network, password))

    def _onKeyboardCancelled(self):
        self.__statusLabel.setText("Connection cancelled")

    async def _onRefreshRequested(self):
        if self.__isConnecting:
            self.__statusLabel.setText("Cannot refresh while connecting...")
            return

        self.__statusLabel.setText("Refreshing networks...")
        self.refreshNetworks()
        self._syncSelection()

    async def _connectToNetwork(self, network, password):
        try:
            await wifiInterface.connectToNetwork(network, password=password)
            self.__isConnecting = False
            self.__connectingNetwork = None
            self.refreshNetworks()
            self.__statusLabel.setText(f"Connected to {network.ssid}")
            self._syncSelection()
        except Exception as error:
            self.__isConnecting = False
            self.__statusLabel.setText(f"Failed to connect: {error}")
            self.refreshNetworks()
            self._syncSelection()

    def _knownNetworkMap(self):
        return {network.ssid: network for network in wifiInterface.getKnownNetworks()}

    def _resetContentContainer(self):
        self.__contentWidget = QWidget()
        self.__contentLayout = QVBoxLayout(self.__contentWidget)
        self.__contentLayout.setContentsMargins(0, 0, 0, 0)
        self.__contentLayout.setSpacing(GUI.SPACING.WIDE)
        self.__scrollArea.setWidget(self.__contentWidget)

    def _syncSelection(self):
        inputInterface = MAIN_WINDOW.getInputInterface()
        if inputInterface is not None:
            primaryButton = self.getPrimaryButton()
            if primaryButton is not None:
                inputInterface.setSelectedButton(primaryButton)

    def _resolveCurrentNetwork(self):
        try:
            return wifiInterface.getCurrentNetwork()
        except Exception:
            return None

    def _buildOrderedNetworks(self, available_networks):
        priority_network = self.__connectingNetwork
        if priority_network is None:
            priority_network = self._resolveCurrentNetwork()

        remaining_networks = list(available_networks)
        ordered_networks = []

        if priority_network is not None and priority_network.ssid:
            matched_network = None
            for network in remaining_networks:
                if network.ssid == priority_network.ssid:
                    matched_network = network
                    break

            if matched_network is None:
                matched_network = priority_network

            ordered_networks.append(matched_network)
            remaining_networks = [network for network in remaining_networks if network.ssid != matched_network.ssid]

        known_networks = self._knownNetworkMap()
        known_available_networks = [network for network in remaining_networks if network.ssid in known_networks]
        other_available_networks = [network for network in remaining_networks if network.ssid not in known_networks]

        return ordered_networks, known_available_networks, other_available_networks

    def refreshNetworks(self):
        self._resetContentContainer()

        self.__networkButtons = []
        self.__primaryButton = None
        pinned_network_button = None

        try:
            available_networks = wifiInterface.getAvailableNetworks()
        except Exception:
            available_networks = []

        priority_networks, known_available_networks, other_available_networks = self._buildOrderedNetworks(available_networks)

        if priority_networks:
            section_label = "Current activity" if self.__isConnecting else "Current network"
            self.__contentLayout.addWidget(self._makeSectionLabel(section_label))
            for index, network in enumerate(priority_networks):
                button = self._makeNetworkButton(network)
                self.__networkButtons.append(button)
                self.__contentLayout.addWidget(button)
                if not self.__isConnecting and index == 0:
                    pinned_network_button = button

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
            self.__primaryButton = self.__refreshButton
        else:
            self.__primaryButton = self.__networkButtons[0]
            self.__refreshButton.setNavDown(self.__primaryButton)
            self.__primaryButton.setNavUp(self.__refreshButton)

            for previous_button, next_button in zip(self.__networkButtons, self.__networkButtons[1:]):
                previous_button.setNavDown(next_button)
                next_button.setNavUp(previous_button)

            if self.__isConnecting:
                for button in self.__networkButtons:
                    button.disable()
            else:
                for button in self.__networkButtons:
                    button.enable()
                if pinned_network_button is not None:
                    pinned_network_button.disable()

        self.__contentLayout.addStretch(1)

    async def showOverlay(self, navBarButton=None):
        self.refreshNetworks()
        self.__closeButton.setNavUp(navBarButton)
        self.__closeButton.setNavDown(self.__refreshButton)
        self.__refreshButton.setNavUp(self.__closeButton)
        self.__statusLabel.setText("")
        self.show()
        self.raise_()

    async def hideOverlay(self):
        self.hide()
        if self.__onClose is not None:
            self.__onClose()