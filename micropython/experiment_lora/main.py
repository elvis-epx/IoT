import LoRaDuplexCallback
from controller import Controller

controller = Controller()
lora = controller.lora
LoRaDuplexCallback.duplexCallback(lora)
