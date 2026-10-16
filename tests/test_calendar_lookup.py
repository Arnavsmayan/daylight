import json
import unittest
from unittest.mock import patch

from tools import get_calendar_events


class CalendarLookupTests(unittest.TestCase):
    @patch("tools.requests.get")
    @patch("tools.requests.post")
    def test_range_uses_et_midnights(self, token_request, event_request):
        token_request.return_value.json.return_value = {"access_token": "test-token"}
        event_request.return_value.json.return_value = {"items": []}

        result = json.loads(get_calendar_events("2026-10-15", "2026-10-31", "refresh-token"))

        self.assertEqual(result["events"], [])
        params = event_request.call_args.kwargs["params"]
        self.assertEqual(params["timeMin"], "2026-10-15T00:00:00-04:00")
        self.assertEqual(params["timeMax"], "2026-11-01T00:00:00-04:00")

    @patch("tools.requests.get")
    @patch("tools.requests.post")
    def test_single_day_handles_dst_change(self, token_request, event_request):
        token_request.return_value.json.return_value = {"access_token": "test-token"}
        event_request.return_value.json.return_value = {"items": []}

        get_calendar_events("2026-11-01", refresh_token="refresh-token")

        params = event_request.call_args.kwargs["params"]
        self.assertEqual(params["timeMin"], "2026-11-01T00:00:00-04:00")
        self.assertEqual(params["timeMax"], "2026-11-02T00:00:00-05:00")

    @patch("tools.requests.get")
    def test_invalid_date_returns_an_error(self, event_request):
        result = json.loads(get_calendar_events("October 15", refresh_token="refresh-token"))
        self.assertIn("YYYY-MM-DD", result["error"])
        event_request.assert_not_called()


if __name__ == "__main__":
    unittest.main()
