import network
import machine 
lan = network.LAN(mdc=machine.Pin(23), mdio=machine.Pin(18), phy_type=network.PHY_LAN8720, phy_addr=1, power=machine.Pin(16), id=0)
lan.active(true)
lan.ifconfig()
