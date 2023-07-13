import LoRaDuplexCallback
from ttgolora import TTGOLoRa

lora = TTGOLoRa().lora
LoRaDuplexCallback.duplexCallback(lora)
