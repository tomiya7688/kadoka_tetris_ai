import json
import socket
import unittest

from tetris.adapters import JsonlApiServer


class JsonlApiServerTests(unittest.TestCase):
    def test_server_binds_only_to_loopback(self):
        server = JsonlApiServer(0, {0})
        try:
            self.assertEqual(server.address[0], "127.0.0.1")
        finally:
            server.close()

    def test_valid_action_is_acknowledged_and_queued(self):
        server = JsonlApiServer(0, {0})
        server.start()
        try:
            response = self._request(
                server.address,
                {"player": 0, "action": "move_left"},
            )
            self.assertEqual(response, {"ok": True, "queued": True})

            actions = server.drain()
            self.assertEqual(len(actions), 1)
            self.assertEqual(actions[0].player, 0)
            self.assertEqual(actions[0].action, "move_left")
        finally:
            server.close()

    def test_disallowed_player_is_rejected_without_queueing(self):
        server = JsonlApiServer(0, {0})
        server.start()
        try:
            response = self._request(
                server.address,
                {"player": 1, "action": "hard_drop"},
            )
            self.assertFalse(response["ok"])
            self.assertIn("unknown player", response["error"])
            self.assertEqual(server.drain(), ())
        finally:
            server.close()

    def test_unknown_fields_are_rejected(self):
        server = JsonlApiServer(0, {0})
        server.start()
        try:
            response = self._request(
                server.address,
                {"player": 0, "action": "move_left", "internal_state": True},
            )
            self.assertFalse(response["ok"])
            self.assertIn("unknown input action fields", response["error"])
            self.assertEqual(server.drain(), ())
        finally:
            server.close()

    def _request(self, address: tuple[str, int], payload: dict) -> dict:
        with socket.create_connection(address, timeout=2) as connection:
            stream = connection.makefile("rwb")
            stream.write((json.dumps(payload) + "\n").encode("utf-8"))
            stream.flush()
            return json.loads(stream.readline().decode("utf-8"))


if __name__ == "__main__":
    unittest.main()
