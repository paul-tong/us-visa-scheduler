import unittest
from unittest.mock import Mock

from test_core import RuntimeTest
from visa_tool.browser import BrowserPort, reschedule_url, retry_seconds, safe_origin
from visa_tool.core import WorkerLost


class URLTests(unittest.TestCase):
    def test_reschedule_allowlist(self):
        self.assertTrue(reschedule_url("https://www.usvisascheduling.com/zh-CN/schedule/?reschedule=true"))
        for value in (
            "https://www.usvisascheduling.com/zh-CN/schedule/",
            "https://www.usvisascheduling.com/zh-CN/AppointmentManager/",
            "https://www.usvisascheduling.com.evil.invalid/zh-CN/schedule/?reschedule=true",
            "https://www.usvisascheduling.com/zh-CN/schedule/?reschedule=true&reschedule=false",
            "http://www.usvisascheduling.com/zh-CN/schedule/?reschedule=true",
        ):
            with self.subTest(value=value):
                self.assertFalse(reschedule_url(value))

    def test_credentials_origin_and_retry_after(self):
        self.assertTrue(safe_origin("https://atlasauth.b2clogin.com/path"))
        self.assertFalse(safe_origin("https://atlasauth.b2clogin.com.evil.invalid/path"))
        self.assertEqual(retry_seconds("120"), 120)
        self.assertEqual(retry_seconds("invalid"), 0)


class WorkerProtocolTests(RuntimeTest):
    def test_long_click_pauses_fit_watchdog_and_progress_is_not_a_result(self):
        port = BrowserPort.__new__(BrowserPort)
        port.config, port.runtime = self.config, self.runtime
        self.config.click_wait_seconds = 30
        port.connection = Mock()
        port.process = Mock()
        replies = [("click_wait", {"action": action, "seconds": 30})
                   for action in ("CALENDAR_YEAR", "CALENDAR_MONTH", "PREFERRED_DATE", "TIME_SLOT")]
        replies.append(("ok", "prepared"))
        port.connection.recv.side_effect = replies
        delays = iter((0, 30, 30, 30, 30))
        port.connection.poll.side_effect = lambda _: self.clock.sleep(next(delays)) or True
        port.close = Mock()
        self.assertEqual(port.call("prepare_slot", "2026-12-23"), "prepared")
        port.close.assert_not_called()
        records = "".join(path.read_text() for path in (self.config.root / "logs").glob("EventLog_*"))
        self.assertEqual(records.count('"action": "CLICK_WAIT"'), 4)

    def test_click_progress_does_not_extend_explicit_deadline(self):
        port = BrowserPort.__new__(BrowserPort)
        port.config, port.runtime = self.config, self.runtime
        port.connection = Mock()
        port.connection.poll.side_effect = lambda _: self.clock.sleep(2) or True
        port.connection.recv.return_value = ("click_wait", {"action": "SUBMIT", "seconds": 30})
        port.close = Mock()
        with self.assertRaises(WorkerLost):
            port._receive(3)
        port.close.assert_called_once_with(force=True)


if __name__ == "__main__":
    unittest.main()
