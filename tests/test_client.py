import unittest

from brennstuhl_webline_client import CommandSet, DeviceResponseError, PremiumWebLineV3Client


class FakeTransport:
    def __init__(self, responses):
        self.responses = responses
        self.sent_commands = []

    def send_command(self, command: str) -> str:
        self.sent_commands.append(command)
        return self.responses[command]


class PremiumWebLineV3ClientTests(unittest.TestCase):
    def setUp(self):
        self.command_set = CommandSet(power_on="CMD_ON", power_off="CMD_OFF", status="CMD_STATUS")

    def test_turn_on_uses_configured_command(self):
        transport = FakeTransport({"CMD_ON": "OK"})
        client = PremiumWebLineV3Client(transport=transport, commands=self.command_set)

        response = client.turn_on()

        self.assertEqual("OK", response)
        self.assertEqual(["CMD_ON"], transport.sent_commands)

    def test_turn_off_uses_configured_command(self):
        transport = FakeTransport({"CMD_OFF": "OK"})
        client = PremiumWebLineV3Client(transport=transport, commands=self.command_set)

        response = client.turn_off()

        self.assertEqual("OK", response)
        self.assertEqual(["CMD_OFF"], transport.sent_commands)

    def test_read_status_uses_configured_command(self):
        transport = FakeTransport({"CMD_STATUS": "ON"})
        client = PremiumWebLineV3Client(transport=transport, commands=self.command_set)

        response = client.read_status()

        self.assertEqual("ON", response)
        self.assertEqual(["CMD_STATUS"], transport.sent_commands)

    def test_empty_response_raises_device_response_error(self):
        transport = FakeTransport({"CMD_STATUS": ""})
        client = PremiumWebLineV3Client(transport=transport, commands=self.command_set)

        with self.assertRaises(DeviceResponseError):
            client.read_status()


if __name__ == "__main__":
    unittest.main()
