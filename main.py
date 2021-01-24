import sys
from PyQt5.QtWidgets import *
from PyQt5.QtGui import QPalette, QColor
from PyQt5.QtCore import Qt
from pyqtlet import L, MapWidget
import serial
import serial.tools.list_ports
import paho.mqtt.client as mqtt

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()

        self.state = {
            "serial": {
                "client": serial.Serial(),
                "connected": False,
                "device": "",
                "baud": 0,
            },
            "mqtt": {
                "client": mqtt.Client(),
                "connected": False,
                "hostname": "",
            }
        }

        self.state["mqtt"]["client"].on_connect = self.mqtt_on_connect
        self.state["mqtt"]["client"].on_disconnect = self.mqtt_on_disconnect
        self.state["mqtt"]["client"].on_subscribe = self.mqtt_on_subscribe
        self.state["mqtt"]["client"].on_unsubscribe = self.mqtt_on_unsubscribe
        self.state["mqtt"]["client"].on_publish = self.mqtt_on_publish
        self.state["mqtt"]["client"].on_message = self.mqtt_on_message
        self.state["mqtt"]["client"].on_log = self.mqtt_on_log

        self.layout_main_window = QGridLayout()

        self.create_map_interface()
        self.create_serial_interface()
        self.create_mqtt_interface()

        self.layout_main_window.addWidget(self.map_widget, 0, 1, -1, -1)
        self.layout_main_window.addWidget(self.groupbox_serial_interface, 0, 0)
        self.layout_main_window.addWidget(self.groupbox_mqtt_interface, 1, 0)

        self.setLayout(self.layout_main_window)

        self.show()

    def create_map_interface(self):
        self.map_widget = MapWidget()
        self.main_map = L.map(self.map_widget)
        self.main_map.setView([37.70, -122.50], 12)
        L.tileLayer('http://{s}.tile.osm.org/{z}/{x}/{y}.png').addTo(self.main_map)

    def create_serial_interface(self):
        self.groupbox_serial_interface = QGroupBox("Serial")
        self.groupbox_serial_interface.setMinimumWidth(320)
        self.groupbox_serial_interface.setMaximumWidth(320)
        self.layout_serial_interface = QGridLayout()
        self.groupbox_serial_interface.setLayout(self.layout_serial_interface)

        self.label_serial_port = QLabel(self)
        self.label_serial_port.setText("Device:")
        self.label_serial_port.setMinimumWidth(100)
        self.label_serial_port.setMaximumWidth(100)

        self.combo_serial_port = QComboBox(self)
        devices = self.serial_list_ports()
        for device in devices:
            self.combo_serial_port.addItem(device)

        self.label_serial_baud_rate = QLabel(self)
        self.label_serial_baud_rate.setText("Baud Rate:")

        self.line_edit_serial_baud_rate = QLineEdit(self)
        self.line_edit_serial_baud_rate.setText("115200")

        self.button_serial_connect = QPushButton(self)
        self.button_serial_connect.setText("Connect")
        self.button_serial_connect.clicked.connect(self.button_serial_connect_clicked)

        self.layout_serial_interface.addWidget(self.label_serial_port, 0, 0)
        self.layout_serial_interface.addWidget(self.combo_serial_port, 0, 1)
        self.layout_serial_interface.addWidget(self.label_serial_baud_rate, 1, 0)
        self.layout_serial_interface.addWidget(self.line_edit_serial_baud_rate, 1, 1)
        self.layout_serial_interface.addWidget(self.button_serial_connect, 2, 0, 1, 2)

    def lock_serial_interface(self):
        self.combo_serial_port.setReadOnly(True)
        self.line_edit_serial_baud_rate.setReadOnly(True)

        self.button_serial_connect.setText("Disconnect")

    def unlock_serial_interface(self):
        self.combo_serial_port.setReadOnly(False)
        self.line_edit_serial_baud_rate.setReadOnly(False)

        self.button_serial_connect.setText("Connect")

    def serial_list_ports(self):
        ports = list(serial.tools.list_ports.comports(False))
        devices = []

        for port in ports:
            devices.append(str(port.description) + " (" + port.device + ")")

        return devices

    def button_serial_connect_clicked(self):
        if not self.state["serial"]["connected"]:
            selected_serial_port = self.combo_serial_port.currentText().split("(")[1].replace(")", "")

            try:
                self.state["serial"]["client"].port = selected_serial_port
                self.state["serial"]["client"].baudrate = int(self.line_edit_serial_baud_rate.text())
                self.state["serial"]["client"].open()

                self.state["serial"]["connected"] = True
                self.state["serial"]["device"] = selected_serial_port
                self.state["serial"]["baud"] = self.line_edit_serial_baud_rate.text()

                self.lock_serial_interface()

                print("Connected to: " + self.combo_serial_port.currentText())
            except serial.SerialException as e:
                print("Failed to connect to Serial Port: " + self.combo_serial_port.currentText())
                print(e)
        else:
            try:
                self.serial_port.close()

                self.state["serial"]["connected"] = False
                self.state["serial"]["device"] = ""
                self.state["serial"]["baud"] = 0

                self.unlock_serial_interface()

                print("Disconnected from: " + self.state["serial"]["device"])
            except serial.SerialException as e:
                print("Failed to disconnect from: " + self.state["serial"]["device"])
                print(e)

    def create_mqtt_interface(self):
        self.groupbox_mqtt_interface = QGroupBox("MQTT")
        self.groupbox_mqtt_interface.setMinimumWidth(320)
        self.groupbox_mqtt_interface.setMaximumWidth(320)
        self.layout_mqtt_interface = QGridLayout()
        self.groupbox_mqtt_interface.setLayout(self.layout_mqtt_interface)

        self.label_mqtt_hostname = QLabel(self)
        self.label_mqtt_hostname.setText("Hostname:")
        self.label_mqtt_hostname.setMinimumWidth(100)
        self.label_mqtt_hostname.setMaximumWidth(100)

        self.line_edit_mqtt_hostname = QLineEdit(self)
        self.line_edit_mqtt_hostname.setText("broker.outoftolerance.com")

        self.label_mqtt_port = QLabel(self)
        self.label_mqtt_port.setText("Port: ")

        self.line_edit_mqtt_port = QLineEdit(self)
        self.line_edit_mqtt_port.setText("8883")

        self.label_mqtt_username = QLabel(self)
        self.label_mqtt_username.setText("Username: ")

        self.line_edit_mqtt_username = QLineEdit(self)
        self.line_edit_mqtt_username.setText("")

        self.label_mqtt_password = QLabel(self)
        self.label_mqtt_password.setText("Password: ")

        self.line_edit_mqtt_password = QLineEdit(self)
        self.line_edit_mqtt_password.setText("")

        self.button_mqtt_connect = QPushButton(self)
        self.button_mqtt_connect.setText("Connect")
        self.button_mqtt_connect.clicked.connect(self.button_mqtt_connect_clicked)

        self.layout_mqtt_interface.addWidget(self.label_mqtt_hostname, 0, 0)
        self.layout_mqtt_interface.addWidget(self.line_edit_mqtt_hostname, 0, 1)
        self.layout_mqtt_interface.addWidget(self.label_mqtt_port, 1, 0)
        self.layout_mqtt_interface.addWidget(self.line_edit_mqtt_port, 1, 1)
        self.layout_mqtt_interface.addWidget(self.label_mqtt_username, 2, 0)
        self.layout_mqtt_interface.addWidget(self.line_edit_mqtt_username, 2, 1)
        self.layout_mqtt_interface.addWidget(self.label_mqtt_password, 3, 0)
        self.layout_mqtt_interface.addWidget(self.line_edit_mqtt_password, 3, 1)
        self.layout_mqtt_interface.addWidget(self.button_mqtt_connect, 4, 0, 1, 2)

    def lock_mqtt_interface(self):
        self.line_edit_mqtt_hostname.setReadOnly(True)
        self.line_edit_mqtt_port.setReadOnly(True)
        self.line_edit_mqtt_username.setReadOnly(True)
        self.line_edit_mqtt_password.setReadOnly(True)

        self.button_mqtt_connect.setText("Disconnect")

    def unlock_mqtt_interface(self):
        self.line_edit_mqtt_hostname.setReadOnly(False)
        self.line_edit_mqtt_port.setReadOnly(False)
        self.line_edit_mqtt_username.setReadOnly(False)
        self.line_edit_mqtt_password.setReadOnly(False)

        self.button_mqtt_connect.setText("Connect")

    def button_mqtt_connect_clicked(self):
        if not self.state["mqtt"]["connected"]:
            self.state["mqtt"]["client"].username_pw_set(self.line_edit_mqtt_username.text(), self.line_edit_mqtt_password.text())
            self.state["mqtt"]["client"].connect(self.line_edit_mqtt_hostname.text(), int(self.line_edit_mqtt_port.text()), 30)
            self.state["mqtt"]["client"].loop_start()
        else:
            self.state["mqtt"]["client"].loop_stop()
            self.state["mqtt"]["client"].disconnect()

    def mqtt_on_connect(self, client, userdata, flags, return_code):
        if return_code == 0:
            print("Connected to MQTT broker at: " + self.line_edit_mqtt_hostname.text())
            self.state["mqtt"]["connected"] = True
            self.state["mqtt"]["hostname"] = self.line_edit_mqtt_hostname.text()
            self.lock_mqtt_interface()
        else:
            print("Failed to connect to MQTT broker at: " + self.line_edit_mqtt_hostname.text())

    def mqtt_on_disconnect(self, client, userdata, return_code):
        if return_code == 0:
            print("Disconnected from MQTT broker")
        else:
            print("Failed to cleanly disconnect from MQTT broker, already disconnected")

        self.state["mqtt"]["connected"] = False
        self.state["mqtt"]["hostname"] = ""
        self.unlock_mqtt_interface()

    def mqtt_on_subscribe(self, client, userdata, message_id, granted_qos):
        print("test")

    def mqtt_on_unsubscribe(self, client, userdata, message_id):
        print("test")

    def mqtt_on_publish(self, client, userdata, message_id):
        print("test")

    def mqtt_on_message(self, client, userdata, message):
        print("test")

    def mqtt_on_log(self, client, userdata, level, string):
        print(level + ", " + string)

if __name__ == '__main__':
    app = QApplication(sys.argv)

    app.setApplicationName("Icarus GCS")

    # Set dark mode theme
    app.setStyle("Fusion")
    palette = QPalette()
    palette.setColor(QPalette.Window, QColor(53, 53, 53))
    palette.setColor(QPalette.WindowText, Qt.white)
    app.setPalette(palette)

    widget = MainWindow()

    sys.exit(app.exec_())