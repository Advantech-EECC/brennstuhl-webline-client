import logging
import os
import sys
import tempfile
import unittest
from io import StringIO
from unittest.mock import patch

from brennstuhl_webline_client.cli import main


class CliOnOffStatusTests(unittest.TestCase):
    def _temp_config_file(self, content: str):
        fd, path = tempfile.mkstemp(suffix=".yaml")
        os.close(fd)
        with open(path, "w", encoding="utf-8") as file:
            file.write(content)
        self.addCleanup(lambda: os.path.exists(path) and os.unlink(path))
        return path

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
        with patch("brennstuhl_webline_client.cli.HttpCgiTransport") as mock_transport_cls, \
             patch("brennstuhl_webline_client.cli.PremiumWebLineV3Client.read_status", return_value="ON"):
            mock_transport_cls.return_value = mock_transport_cls
            main(
                [
                    "192.168.1.2",
                    "--port",
                    "1234",
                    "--timeout",
                    "5.0",
                    "--username",
                    "user",
                    "--password",
                    "pass",
                    "status",
                ]
            )

        mock_transport_cls.assert_called_once_with(
            host="192.168.1.2",
            port=1234,
            timeout_seconds=5.0,
            username="user",
            password="pass",
        )

    def test_relay_argument_is_forwarded_to_client(self):
        with patch("brennstuhl_webline_client.cli.PremiumWebLineV3Client") as mock_client_cls:
            mock_client = mock_client_cls.return_value
            mock_client.read_status.return_value = "OFF"
            with patch("sys.stdout", new_callable=StringIO):
                main(["192.168.1.2", "--relay", "1", "status"])

        mock_client_cls.assert_called_once()
        self.assertEqual(1, mock_client_cls.call_args.kwargs["relay"])

    def test_verbose_enables_debug_logging(self):
        with patch("brennstuhl_webline_client.cli.logging.basicConfig") as mock_basic_config:
            self._run(["192.168.1.1", "--verbose", "status"], "read_status", "ON")
        mock_basic_config.assert_called_once_with(
            level=logging.DEBUG,
            format="%(levelname)s:%(name)s:%(message)s",
        )

    def test_config_can_provide_host_and_command(self):
        config_path = self._temp_config_file(
            "host: 192.168.1.3\n"
            "command: status\n"
            "relay: 1\n"
        )
        with patch("brennstuhl_webline_client.cli.HttpCgiTransport") as mock_transport_cls, patch(
            "brennstuhl_webline_client.cli.PremiumWebLineV3Client.read_status", return_value="ON"
        ):
            mock_transport_cls.return_value = mock_transport_cls
            exit_code = main(["--config", config_path])

        self.assertEqual(0, exit_code)
        mock_transport_cls.assert_called_once_with(
            host="192.168.1.3",
            port=80,
            timeout_seconds=2.0,
            username=None,
            password=None,
        )

    def test_cli_values_override_config(self):
        config_path = self._temp_config_file(
            "host: 192.168.1.10\n"
            "command: off\n"
            "port: 80\n"
            "timeout: 2.0\n"
        )
        with patch("brennstuhl_webline_client.cli.HttpCgiTransport") as mock_transport_cls, patch(
            "brennstuhl_webline_client.cli.PremiumWebLineV3Client.read_status", return_value="ON"
        ):
            mock_transport_cls.return_value = mock_transport_cls
            exit_code = main(["--config", config_path, "192.168.1.4", "--port", "1234", "status"])

        self.assertEqual(0, exit_code)
        mock_transport_cls.assert_called_once_with(
            host="192.168.1.4",
            port=1234,
            timeout_seconds=2.0,
            username=None,
            password=None,
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

    def test_missing_host_without_config_exits_with_error(self):
        with self.assertRaises(SystemExit) as cm:
            main(["status"])
        self.assertNotEqual(0, cm.exception.code)


if __name__ == "__main__":
    unittest.main()
