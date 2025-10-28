"""Small demo showing DeviceRegistry usage and a fake Pump implementation.

Run with: python test/test.py
"""

import sys
import pathlib
import asyncio

# When running the test script directly, ensure the project root is on sys.path
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from devices.devices import DeviceRegistry
from devices.pumps import Pump


class FakePump(Pump):
	def __init__(self, name: str):
		super().__init__(name)

	async def connect(self):
		await asyncio.sleep(0.01)
		self._connected = True
		print(f"{self.name}: connected")

	async def disconnect(self):
		await asyncio.sleep(0.005)
		self._connected = False
		print(f"{self.name}: disconnected")

	async def start(self):
		print(f"{self.name}: start command")

	async def stop(self):
		print(f"{self.name}: stop command")

	async def run(self):
		# simple run loop for demo
		while self._connected:
			await asyncio.sleep(0.1)
			print(f"{self.name}: running heartbeat")

	async def set_rate(self, rate: float) -> None:
		print(f"{self.name}: set_rate={rate}")

	async def dispense(self, volume: float) -> None:
		print(f"{self.name}: dispense {volume}")


async def main():
	registry = DeviceRegistry()
	pump = FakePump('pump_demo')

	registry.register('pumps', pump.name, pump)
	print('Registered pumps:', registry.list_names('pumps'))

	# connect, start, and run in background
	await pump.connect()
	await pump.set_rate(1.5)
	pump.background()

	# let the background loop run a bit
	await asyncio.sleep(0.35)
	await pump.disconnect()


if __name__ == '__main__':
	asyncio.run(main())

