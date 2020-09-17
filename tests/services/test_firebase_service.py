
from tests.base_test import BaseTest
from communicator.services.firebase_service import FirebaseService


class FirebaseServiceTest(BaseTest):

    def test_get_samples(self):
        service = FirebaseService()
        samples = service.get_samples()

