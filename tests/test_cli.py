import sys
import unittest
from io import StringIO
from unittest.mock import patch

from brennstuhl_webline_client.cli import main


class CliOnOffStatusTests(unittest.TestCase):
    def _run(self, argv, client_method, device_response="OK"):
        with patch(f"brennstuhl_webline_client.cli.PremiumWebLineV3Client.{client_method}", return_value=device_response) as mock_method:
            with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
                exit_code = main(argv)
        return exit_code, mock_stdout.getvalue().strip(), mock_method

    def test_on_subcommand_calls_turn_on_and_prints_response(self):
        exit_code, output, mock_method = self._run(["192.168.1.1", "on"], "turn_on")

        self.assertEqual(0, exit_code)
        self.assertEqual("OK", output)
        mock_method.assert_called_once()

    def test_off_subcommand_calls_turn_off_and_prints_response(self):
        exit_code, output, mock_method = self._run(["192.168.1.1", "off"], "turn_off")

        self.assertEqual(0, exit_code)
        self.assertEqual("OK", output)
        mock_method.assert_called_once()

    def test_status_subcommand_calls_read_status_and_prints_response(self):
        exit_code, output, mock_method = self._run(["192.168.1.1", "status"], "read_status", "ON")

        self.assertEqual(0, exit_code)
        self.assertEqual("ON", output)
        mock_method.assert_called_once()

    def test_custom_port_and_timeout_are_passed_to_transport(self):
        with patch("brennstuhl_webline_client.cli.LineBasedSocketTransport") as mock_transport_cls, \
             patch("brennstuhl_webline_client.cli.PremiumWebLineV3Client.read_status", return_value="ON"):
            mock_transport_cls.return_value = mock_transport_cls
            main(["192.168.1.2", "--port", "1234", "--timeout", "5.0", "status"])

        mock_transport_cls.assert_called_once_with(
            host="192.168.1.2",
            port=1234,
            timeout_seconds=5.0,
        )

    def test_transport_error_prints_to_stderr_and_returns_1(self):
        from brennstuhl_webline_client import DeviceTransportError

        with patch("brennstuhl_webline_client.cli.PremiumWebLineV3Client.turn_on", side_effect=DeviceTransportError("no route")):
            with patch("sys.stderr", new_callable=StringIO) as mock_stderr:
                exit_code = main(["192.168.1.1", "on"])

        self.assertEqual(1, exit_code)
        self.assertIn("no route", mock_stderr.getvalue())

    def test_response_error_prints_to_stderr_and_returns_1(self):
        from brennstuhl_webline_client import DeviceResponseError

        with patch("brennstuhl_webline_client.cli.PremiumWebLineV3Client.read_status", side_effect=DeviceResponseError("empty")):
            with patch("sys.stderr", new_callable=StringIO) as mock_stderr:
                exit_code = main(["192.168.1.1", "status"])

        self.assertEqual(1, exit_code)
        self.assertIn("empty", mock_stderr.getvalue())

    def test_missing_subcommand_exits_with_error(self):
        with self.assertRaises(SystemExit) as cm:
            main(["192.168.1.1"])
        self.assertNotEqual(0, cm.exception.code)


if __name__ == "__main__":
    unittest.main()
