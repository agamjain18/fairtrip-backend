import firebase_admin
from firebase_admin import credentials, messaging
import os
from typing import List, Optional
import json

class FirebaseService:
    _initialized = False

    @classmethod
    def initialize(cls):
        if cls._initialized:
            return

        service_account_path = os.getenv("FIREBASE_SERVICE_ACCOUNT_PATH")
        if service_account_path and os.path.exists(service_account_path):
            try:
                cred = credentials.Certificate(service_account_path)
                firebase_admin.initialize_app(cred)
                cls._initialized = True
                print("✅ Firebase Admin initialized successfully from file")
            except Exception as e:
                print(f"❌ Error initializing Firebase Admin: {e}")
        else:
            # Fallback to default credentials (works on Google Cloud) or skip
            try:
                firebase_admin.initialize_app()
                cls._initialized = True
                print("✅ Firebase Admin initialized with default credentials")
            except Exception as e:
                print(f"⚠️ Firebase Admin initialization failed (Expected if not on GCP/No key): {e}")

    @staticmethod
    def send_push_notification(token: str, title: str, body: str, data: Optional[dict] = None):
        """Send a single push notification"""
        if not FirebaseService._initialized:
            FirebaseService.initialize()
            if not FirebaseService._initialized:
                print("⚠️ Cannot send push notification: Firebase not initialized")
                return

        message = messaging.Message(
            notification=messaging.Notification(
                title=title,
                body=body,
            ),
            data=data or {},
            token=token,
        )

        try:
            response = messaging.send(message)
            print(f"✅ Successfully sent push notification: {response}")
            return response
        except Exception as e:
            print(f"❌ Error sending push notification: {e}")
            return None

    @staticmethod
    def send_multicast_notification(tokens: List[str], title: str, body: str, data: Optional[dict] = None):
        """Send notification to multiple tokens"""
        if not FirebaseService._initialized:
            FirebaseService.initialize()
            if not FirebaseService._initialized:
                return

        if not tokens:
            return

        message = messaging.MulticastMessage(
            notification=messaging.Notification(
                title=title,
                body=body,
            ),
            data=data or {},
            tokens=tokens,
        )

        try:
            response = messaging.send_multicast(message)
            print(f"✅ Successfully sent multicast notification: {response.success_count} success, {response.failure_count} failure")
            return response
        except Exception as e:
            print(f"❌ Error sending multicast notification: {e}")
            return None
