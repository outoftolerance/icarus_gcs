import time

class Icarus():
	@property
	def id(self):
		return self._id
	
	@property
	def telemetry(self):
		return self._telemetry
	
	def __init__(self, id):
		super().__init__()

		self._state = {
			"location": {
				"set": False,
			}
		}

		self._id = id

		self._tolc = 0

		self._telemetry = {
			"latitude": 0.0,
			"longitude": 0.0,
			"altitude": 0.0,
			"altitude_elipsoid": 0.0,
			"altitude_relative": 0.0,
			"altitude_barometric": 0.0,
			"velocity_horizontal": 0.0,
			"velocity_vertical": 0.0,
			"roll": 0.0,
			"pitch": 0.0,
			"yaw": 0.0,
			"heading": 0.0,
			"course": 0.0,
			"temperature": 0.0,
			"pressure": 0.0,
			"humidity": 0.0,
			"hdop": 0.0,
			"fix": 0,
		}

	def tslc(self):
		return round(time.time()) - self.tolc

	def location(self):
		return [
			self.telemetry["latitude"], 
			self.telemetry["longitude"], 
			self.telemetry["altitude"]
		]

	def location_detailed(self):
		return [
			self.telemetry["latitude"], 
			self.telemetry["longitude"], 
			self.telemetry["altitude"],
			self.telemetry["altitude_elipsoid"],
			self.telemetry["altitude_relative"],
			self.telemetry["altitude_barometric"]
		]

	def location_status(self):
		return [
			self.telemetry["hdop"],
			self.telemetry["fix"]
		]

	def orientation(self):
		return [
			self.telemetry["roll"], 
			self.telemetry["pitch"], 
			self.telemetry["yaw"],
			self.telemetry["heading"]
		]

	def movement(self):
		return [
			self.telemetry["velocity_horizontal"], 
			self.telemetry["velocity_vertical"], 
			self.telemetry["course"]
		]

	def environment(self):
		return [
			self.telemetry["temperature"], 
			self.telemetry["pressure"], 
			self.telemetry["humidity"]
		]