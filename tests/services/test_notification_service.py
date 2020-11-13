from datetime import datetime

import pytz

from tests.base_test import BaseTest


from communicator import app
from communicator.models import Sample
from communicator.services.notification_service import TEST_MESSAGES, NotificationService


class TestNotificationService(BaseTest):

    def test_send_notification(self):
        message_count = len(TEST_MESSAGES)
        sample = Sample(email="dan@stauntonmakerspace.com", result_code="1234")
        with NotificationService(app) as notifier:
            notifier.send_result_email(sample)
        self.assertEqual(len(TEST_MESSAGES), message_count + 1)
        self.assertEqual("UVA: BE SAFE Notification", self.decode(TEST_MESSAGES[-1]['subject']))

    def test_send_sms_notification_with_no_email(self):
        message_count = len(TEST_MESSAGES)
        sample = Sample(phone="540-457-0024", result_code="1234")
        with NotificationService(app) as notifier:
            notifier.send_result_sms(sample)
        self.assertEqual(len(TEST_MESSAGES), message_count + 1)
        self.assertEqual("Dear Student, You have an important notification from UVA, "
                         "please visit: https://besafe.virginia.edu/result-demo?code=1234. "
                         "Reply 'STOP' to opt-out.",
                         TEST_MESSAGES[-1])

    def test_send_sms_notification_is_personalized(self):
        message_count = len(TEST_MESSAGES)
        sample = Sample(phone="540-457-0024", email="dhf8r@virginia.edu", result_code="1234")
        with NotificationService(app) as notifier:
            notifier.send_result_sms(sample)
        self.assertEqual(len(TEST_MESSAGES), message_count + 1)
        self.assertEqual("Dear dhf8r, You have an important notification from UVA, "
                         "please visit: https://besafe.virginia.edu/result-demo?code=1234. "
                         "Reply 'STOP' to opt-out.",
                         TEST_MESSAGES[-1])
