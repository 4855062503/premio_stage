import json
import tempfile
import logging

import firebase_admin
from firebase_admin import credentials, messaging

logger = logging.getLogger(__name__)

class FCM:
    def __init__(self, firebase_credentials):
        if firebase_credentials.endswith('.json'):
            self.init_firebase(firebase_credentials)
        else:
            try:
                json.loads(firebase_credentials)
                with tempfile.NamedTemporaryFile(mode='w') as fp:
                    fp.write(firebase_credentials)
                    fp.flush()
                    self.init_firebase(fp.name)
            except Exception as e: # pylint: disable=broad-except
                logger.error(e)
                logger.error('"firebase_credentials" failed to load from json')

    def init_firebase(self, cred_filename):
        logger.info('loading firebase creds from "%s"', cred_filename)
        cred = credentials.Certificate(cred_filename)
        self.default_app = firebase_admin.initialize_app(cred)
        logger.info('loading firebase creds')

    def send_to_token(self, registration_token, title, body, image):
        message = messaging.Message(
            notification=messaging.Notification(title=title, body=body, image=image),
            token=registration_token,
        )
        messaging.send(message)

    def send_to_topic(self, topic, title, body, image):
        message = messaging.Message(
            notification=messaging.Notification(title=title, body=body, image=image),
            topic=topic,
        )
        messaging.send(message)

    def subscribe_to_topics(self, registration_token, topics):
        registration_tokens = [registration_token]
        for topic in topics:
            messaging.subscribe_to_topic(registration_tokens, topic)
