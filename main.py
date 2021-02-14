import sys, io, os, time, json, configparser, socket

from PyQt5 import Qt, QtCore
from PyQt5.QtCore import Qt, QTimer, QDateTime, QSize
from PyQt5.QtWidgets import *
from PyQt5.QtGui import QPalette, QColor, QIcon
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtWebChannel import QWebChannel

import serial
import serial.tools.list_ports
import paho.mqtt.client as mqtt
import matplotlib
matplotlib.use('Qt5Agg')

from map_wrapper import MapWrapper
from icarus import Icarus

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()

        # Init a state dict
        self.state = {
            "internet": {
                "connected": False,
            },
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
                "port": "",
                "username": "",
            }
        }

        # Grab config
        self.config = configparser.ConfigParser()
        self.config.read('config.ini')

        # Setup MQTT Callbacks
        self.state["mqtt"]["client"].on_connect = self.mqtt_on_connect
        self.state["mqtt"]["client"].on_disconnect = self.mqtt_on_disconnect
        self.state["mqtt"]["client"].on_subscribe = self.mqtt_on_subscribe
        self.state["mqtt"]["client"].on_unsubscribe = self.mqtt_on_unsubscribe
        self.state["mqtt"]["client"].on_publish = self.mqtt_on_publish
        self.state["mqtt"]["client"].on_message = self.mqtt_on_message
        self.state["mqtt"]["client"].on_log = self.mqtt_on_log

        # Setup support things
        self.create_icons()

        # Setup main window
        self.layout_main_window = QGridLayout()

        self.setWindowTitle("Icarus GCS")
        self.setWindowIcon(QIcon('assets/balloon_map_icon.png'))

        self.create_toolbar_interface()
        self.create_map_interface()
        self.create_serial_interface()
        self.create_mqtt_interface()

        self.layout_main_window.addWidget(self.toolbar_status, 0, 1, 1, -1)
        self.layout_main_window.addWidget(self.webengine_map, 1, 1, -1, -1)
        self.layout_main_window.addWidget(self.groupbox_serial_interface, 0, 0, 2, 1)
        self.layout_main_window.addWidget(self.groupbox_mqtt_interface, 2, 0)

        self.setLayout(self.layout_main_window)

        # Setup timers for events
        self.timer_internet_status=QTimer(self)
        self.timer_internet_status.timeout.connect(self.on_timer_internet_status)
        self.timer_internet_status.start(5 * 1000)

        # Check timed events once at the start
        self.on_timer_internet_status()

        # Let's do this!
        self.show()

    def create_toolbar_interface(self):
        self.toolbar_status = QToolBar()
        self.toolbar_status.setFloatable(False)
        self.toolbar_status.setMovable(False)
        self.toolbar_status.setIconSize(QSize(24, 24))

        self.toolbutton_internet_status = QToolButton()
        self.toolbutton_internet_status.setIcon(self.icons["cloud-line"])
        self.toolbutton_internet_status.setEnabled(False)

        self.toolbutton_mqtt_status = QToolButton()
        self.toolbutton_mqtt_status.setIcon(self.icons["server-line"])
        self.toolbutton_mqtt_status.setEnabled(False)

        self.toolbutton_radio_status = QToolButton()
        self.toolbutton_radio_status.setIcon(self.icons["wifi-line"])
        self.toolbutton_radio_status.setEnabled(False)

        self.toolbutton_cellular_status = QToolButton()
        self.toolbutton_cellular_status.setIcon(self.icons["sim-card-line"])
        self.toolbutton_cellular_status.setEnabled(False)

        self.toolbutton_heartbeat_status = QToolButton()
        self.toolbutton_heartbeat_status.setIcon(self.icons["heart-line"])
        self.toolbutton_heartbeat_status.setEnabled(False)

        self.toolbar_status.addWidget(self.toolbutton_internet_status)
        self.toolbar_status.addWidget(self.toolbutton_mqtt_status)
        self.toolbar_status.addWidget(self.toolbutton_radio_status)
        self.toolbar_status.addWidget(self.toolbutton_cellular_status)
        self.toolbar_status.addWidget(self.toolbutton_heartbeat_status)

    def create_map_interface(self):
        self.map_wrapper = MapWrapper([
            self.config["Map"]["Home Latitude"],
            self.config["Map"]["Home Longitude"],
        ])

        self.webengine_map = QWebEngineView()
        self.map_view_webchannel = QWebChannel()
        self.map_view_webchannel.registerObject("python_link", self.map_wrapper)
        self.webengine_map.page().setWebChannel(self.map_view_webchannel)
        self.webengine_map.load(QtCore.QUrl.fromLocalFile(QtCore.QDir.current().filePath("static/map.html")))
        self.webengine_map.setMinimumWidth(1024)
        self.webengine_map.setMinimumHeight(768)

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

        self.label_internet_status = QLabel(self)
        self.label_internet_status.setText("Internet:")
        self.label_internet_status.setMinimumWidth(100)
        self.label_internet_status.setMaximumWidth(100)

        self.line_edit_internet_status = QLineEdit(self)
        self.line_edit_internet_status.setText("Disconnected")
        self.line_edit_internet_status.setReadOnly(True)

        self.label_mqtt_hostname = QLabel(self)
        self.label_mqtt_hostname.setText("Hostname:")

        self.line_edit_mqtt_hostname = QLineEdit(self)
        self.line_edit_mqtt_hostname.setText(self.config["MQTT"]["Hostname"])

        self.label_mqtt_port = QLabel(self)
        self.label_mqtt_port.setText("Port: ")

        self.line_edit_mqtt_port = QLineEdit(self)
        self.line_edit_mqtt_port.setText(self.config["MQTT"]["Port"])

        self.label_mqtt_username = QLabel(self)
        self.label_mqtt_username.setText("Username: ")

        self.line_edit_mqtt_username = QLineEdit(self)
        self.line_edit_mqtt_username.setText(self.config["MQTT"]["Username"])

        self.label_mqtt_password = QLabel(self)
        self.label_mqtt_password.setText("Password: ")

        self.line_edit_mqtt_password = QLineEdit(self)
        self.line_edit_mqtt_password.setText(self.config["MQTT"]["Password"])
        self.line_edit_mqtt_password.setEchoMode(QLineEdit.Password)

        self.button_mqtt_connect = QPushButton(self)
        self.button_mqtt_connect.setText("Connect")
        self.button_mqtt_connect.clicked.connect(self.button_mqtt_connect_clicked)

        self.label_mqtt_topic = QLabel(self)
        self.label_mqtt_topic.setText("Topic:")

        self.line_edit_mqtt_topic = QLineEdit(self)

        self.button_mqtt_subscribe = QPushButton(self)
        self.button_mqtt_subscribe.setText("Subscribe")
        #self.button_mqtt_subscribe.clicked.connect(self.button_mqtt_subscribe_clicked)

        self.list_box_mqtt_subscriptions = QListWidget(self)
        self.list_box_mqtt_subscriptions.setMaximumHeight(100)

        self.button_mqtt_unsubscribe = QPushButton(self)
        self.button_mqtt_unsubscribe.setText("Unsubscribe")
        #self.button_mqtt_unsubscribe.clicked.connect(self.button_mqtt_unsubscribe_clicked)

        self.layout_mqtt_interface.addWidget(self.label_internet_status, 0, 0)
        self.layout_mqtt_interface.addWidget(self.line_edit_internet_status, 0, 1)
        self.layout_mqtt_interface.addWidget(self.label_mqtt_hostname, 1, 0)
        self.layout_mqtt_interface.addWidget(self.line_edit_mqtt_hostname, 1, 1)
        self.layout_mqtt_interface.addWidget(self.label_mqtt_port, 2, 0)
        self.layout_mqtt_interface.addWidget(self.line_edit_mqtt_port, 2, 1)
        self.layout_mqtt_interface.addWidget(self.label_mqtt_username, 3, 0)
        self.layout_mqtt_interface.addWidget(self.line_edit_mqtt_username, 3, 1)
        self.layout_mqtt_interface.addWidget(self.label_mqtt_password, 4, 0)
        self.layout_mqtt_interface.addWidget(self.line_edit_mqtt_password, 4, 1)
        self.layout_mqtt_interface.addWidget(self.button_mqtt_connect, 5, 0, 1, 2)
        self.layout_mqtt_interface.addWidget(self.label_mqtt_topic, 6, 0)
        self.layout_mqtt_interface.addWidget(self.line_edit_mqtt_topic, 6, 1)
        self.layout_mqtt_interface.addWidget(self.button_mqtt_subscribe, 7, 0, 1, 2)
        self.layout_mqtt_interface.addWidget(self.list_box_mqtt_subscriptions, 8, 0, 1, 2)
        self.layout_mqtt_interface.addWidget(self.button_mqtt_unsubscribe, 9, 0, 1, 2)

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

    def create_chart_interface(self):
        fig = Figure(figsize=(100, 100), dpi=100)
        self.axes = fig.add_subplot(111)
        fig.axes.plot([0,1,2,3,4], [10,1,20,3,40])

        self.wid
        self.layout_chart_interface = QGridLayout()


    def on_timer_internet_status(self):
        try:
            socket.create_connection(("1.1.1.1", 53))
            self.state["internet"]["connected"] = True
            self.line_edit_internet_status.setText("Connected")
            self.toolbutton_internet_status.setIcon(self.icons["cloud"])
            return True
        except OSError:
            pass

        self.state["internet"]["connected"] = False
        self.line_edit_internet_status.setText("Disconnected")
        self.toolbutton_internet_status.setIcon(self.icons["cloud-line"])
        return False

    def mqtt_on_connect(self, client, userdata, flags, return_code):
        if return_code == 0:
            print("Connected to MQTT broker at: " + self.line_edit_mqtt_hostname.text())
            self.state["mqtt"]["connected"] = True
            self.state["mqtt"]["hostname"] = self.line_edit_mqtt_hostname.text()
            self.state["mqtt"]["port"] = self.line_edit_mqtt_port.text()
            self.state["mqtt"]["username"] = self.line_edit_mqtt_username.text()
            self.toolbutton_mqtt_status.setIcon(self.icons["server"])
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
        self.state["mqtt"]["port"] = ""
        self.state["mqtt"]["username"] = ""
        self.toolbutton_mqtt_status.setIcon(self.icons["server-line"])
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

    def create_icons(self):
        self.icons = {}

        icon_path = "assets/remix/icons"

        self.icons["cloud"] = QIcon(icon_path + "/Business/cloud-fill.svg")
        self.icons["cloud-line"] = QIcon(icon_path + "/Business/cloud-line.svg")
        self.icons["cloud-off"] = QIcon(icon_path + "/Business/cloud-off-fill.svg")
        self.icons["wifi"] = QIcon(icon_path + "/Device/signal-wifi-fill.svg")
        self.icons["wifi-line"] = QIcon(icon_path + "/Device/signal-wifi-line.svg")
        self.icons["server"] = QIcon(icon_path + "/Device/server-fill.svg")
        self.icons["server-line"] = QIcon(icon_path + "/Device/server-line.svg")
        self.icons["wifi-off"] = QIcon(icon_path + "/Device/signal-wifi-off-fill.svg")
        self.icons["radio"] = QIcon(icon_path + "/Device/wifi-fill.svg")
        self.icons["radio-off"] = QIcon(icon_path + "/Device/wifi-off-fill.svg")
        self.icons["sim-card"] = QIcon(icon_path + "/Device/sim-card-2-fill.svg")
        self.icons["sim-card-line"] = QIcon(icon_path + "/Device/sim-card-2-line.svg")
        self.icons["takeoff"] = QIcon(icon_path + "/Map/flight-takeoff-fill.svg")
        self.icons["land"] = QIcon(icon_path + "/Map/flight-land-fill.svg")
        self.icons["heart"] = QIcon(icon_path + "/Health/heart-3-fill.svg")
        self.icons["heart-line"] = QIcon(icon_path + "/Health/heart-3-line.svg")
        self.icons["heart-off"] = QIcon(icon_path + "/Health/dislike-fill.svg")
        self.icons["heart-pulse"] = QIcon(icon_path + "/Health/heart-pulse-fill.svg")

if __name__ == '__main__':
    app = QApplication(sys.argv)

    app.setApplicationName("Icarus GCS")

    # Set dark mode theme
    app.setStyle("Fusion")
    '''
    palette = QPalette()
    palette.setColor(QPalette.Window, QColor(53, 53, 53))
    palette.setColor(QPalette.WindowText, Qt.white)
    app.setPalette(palette)
    '''

    widget = MainWindow()

    sys.exit(app.exec_())