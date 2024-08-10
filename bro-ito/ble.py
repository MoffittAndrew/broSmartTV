# Only import what is necessary
# saves memory and power
from asyncio import sleep_ms, create_task, run
from aioble import Service as aioble_Service, Characteristic as aioble_Characteristic, register_services as aioble_register_services, advertise as aioble_advertise
from bluetooth import UUID, BLE
from micropython import const
from machine import Pin, Timer


_REMOTE_NAME = "bro-ito"
# org.bluetooth.service.media_control
_SERVICE_UUID = UUID(0x1849)
# org.bluetooth.characteristic.media_control_point
_CHARACTERISTIC_UUID = UUID(0x2BA5)
# org.bluetooth.characteristic.gap.appearance.xml
_ADV_APPEARANCE_GENERIC_REMOTE_CONTROL = const(384)

# How frequently to send advertising beacons.
_ADV_INTERVAL_MS = 250_000
# How long to wait after connecting to start sending signals
_INIT_WAIT_MS = 2250
# How frequently to send signals in the backlog.
_SEND_INTERVAL_MS = 50
# How frequently to check for button presses
_BUTTON_INTERVAL_MS = 25
# Disconnect after this many seconds of inactivity
_INACTIVITY_TIMEOUT = 300

button_lookup = [
    "POWER",
    "NAV_RIGHT",
    "NAV_DOWN",
    "MIC",
    "VOL_DOWN",
    "VOL_UP",
    "RETURN",
    "MENU",
    "NAV_LEFT",
    "SELECT",
    "NAV_UP",
    "HOME",
]


class LED:
    def __init__(this):
        this.__led = Pin("LED", Pin.OUT)
        this.__timer = Timer()
        this.__blinking = False
        this.__blink_freq = 8
        
    def __blink(this, timer):
        this.__led.toggle()
        
    def on(this):
        this.__led.on()
        if this.__blinking:
            this.stop_blink()
        
    def off(this):
        this.__led.off()
        if this.__blinking:
            this.stop_blink()
        
    def start_blink(this):
        this.__timer.init(freq=this.__blink_freq, mode=Timer.PERIODIC, callback=this.__blink)
        this.__blinking = True
    
    def stop_blink(this):
        this.__timer.deinit()
        this.__blinking = False
        
        
        
class Inactivity_Timer:
    def __init__(this):
        print()
        
    def reset(this):
        this.__timer = _INACTIVITY_TIMEOUT

    async def start_countdown(this, conn):
        this.reset()
        while this.__timer > 0 and conn.is_connected():                
            
            await _sleep_ms(1000)
            this.__timer -= 1
            
        if conn.is_connected():
            print(f"No activity detected in past {_INACTIVITY_TIMEOUT} seconds, disconnecting BLE...")



class Signal_Sender:
    def __init__(this, char, inactivity_timer):
        this.__char = char
        this.__inactivity_timer = inactivity_timer
        this.__conn = None
        this.__backlog = []
        this.__processing = False
        
    def __send(this, data):
        this.__char.notify(this.__conn, data)
        this.__inactivity_timer.reset()
        
    def send_signal(this, signal):
        this.__backlog.append(signal)
        if not this.__processing:
            print(f"Adding signal {signal} to signal backlog...")
            
    def start_processing(this, conn):
        this.__conn = conn
        this.__processing = True
        this.__process_backlog_task = create_task(this.__process_backlog())
        
    def stop(this):
        this.__processing = False
        this.__process_backlog_task.cancel()
        
    async def __process_backlog(this):
        await sleep_ms(_INIT_WAIT_MS)
        print("Now processing signal backlog")
        while True:
            await sleep_ms(_SEND_INTERVAL_MS)
            if this.__processing and len(this.__backlog) > 0:
                if this.__conn:
                    signal = this.__backlog[0]
                    print(f"Sending signal {signal}...")
                    this.__send(_encode_data(signal))
                    del this.__backlog[0]
                else:
                    print("Cannot process signal backlog, no connection established!")


def _encode_data(data):
    return b"%s" % data
    

async def read_button_task(ble_sender, buttons, active_button_index):
    button_backup = []
    for button in buttons:
        button_backup.append(button.value())
    
    data = button_lookup[active_button_index]
    print(f"BLE initialised with button {data}")
    ble_sender.send_signal(data)
    button_backup[active_button_index] = 1
    
    while True:
        await sleep_ms(_BUTTON_INTERVAL_MS)
        for i in range(len(buttons)):
            val = buttons[i].value()
            if val != button_backup[i]:
                if val:
                    # Send button signal
                    ble_sender.send_signal(button_lookup[i])
                else:
                    # Send signal when button is released
                    ble_sender.send_signal(f"RELEASED_{button_lookup[i]}")
                button_backup[i] = val

async def run_ble(buttons, active_button_index):
    
    led = LED()
    led.start_blink()
    
    # Register GATT server.
    remote_service = aioble_Service(_SERVICE_UUID)
    remote_characteristic = aioble_Characteristic(
        remote_service, _CHARACTERISTIC_UUID, read=True, notify=True
    )
    aioble_register_services(remote_service)
    
    inactivity_timer = Inactivity_Timer()
    
    ble_sender = Signal_Sender(remote_characteristic, inactivity_timer)
    button_task = create_task(read_button_task(ble_sender, buttons, active_button_index))
    
    print("Advertising...")
    async with await aioble_advertise(
        _ADV_INTERVAL_MS,
        name=_REMOTE_NAME,
        services=[_SERVICE_UUID],
        appearance=_ADV_APPEARANCE_GENERIC_REMOTE_CONTROL,
    ) as connection:
        print(f"Connection from {connection.device}")
        ble_sender.start_processing(connection)
        await sleep_ms(_INIT_WAIT_MS)
        led.on()
        await inactivity_timer.start_countdown(connection)
        
    print("Disconnected.")
    button_task.cancel()
    ble_sender.stop()
    led.off()
    
    print("Shutting down BLE...")
    BLE().active(False)
    
def main(buttons, active_button_index):
    run(run_ble(buttons, active_button_index))
    print("Entering sleep mode...")
