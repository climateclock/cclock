from adafruit_esp32spi import adafruit_esp32spi as esp32spi
from adafruit_esp32spi import adafruit_esp32spi_socket as socklib
import board
import digitalio


def init_esp():
    esp = esp32spi.ESP_SPIcontrol(
        board.SPI(),
        digitalio.DigitalInOut(board.ESP_CS),
        digitalio.DigitalInOut(board.ESP_BUSY),
        digitalio.DigitalInOut(board.ESP_RESET)
    )
    socklib.set_interface(esp)
    return esp
