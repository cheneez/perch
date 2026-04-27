import json
import random
import re
import time
from itertools import cycle
from threading import Lock
from urllib.parse import quote
from typing import Any

from locust import HttpUser, between, events, task
from websocket import WebSocket, WebSocketException

try:
    from .config import get_int_env
    from .datasets import load_dataset
except ImportError:
    # Support direct locust -f execution from this directory.
    from config import get_int_env
    from datasets import load_dataset


LISTING_ID_PATTERN = re.compile(r"/listings/property/(\d+)/")
OWNER_LISTING_ID_PATTERN = re.compile(r"/listings/(\d+)/")


dataset = load_dataset()
student_credentials_cycle = cycle(dataset["students"])
lessor_credentials_cycle = cycle(dataset["lessors"])
student_cycle_lock = Lock()
lessor_cycle_lock = Lock()


def _extract_listing_ids(html: str) -> list[int]:
    return [int(match) for match in LISTING_ID_PATTERN.findall(html)]


def _extract_csrf_cookie(user: HttpUser) -> str:
    return user.client.cookies.get("csrftoken", "")


class BasePerchUser(HttpUser):
    wait_time = between(1, 4)
    request_timeout = 10
    abstract = True

    username = ""
    password = ""
    email = ""
    listing_ids: list[int]
    conversation_ids: list[int]

    def on_start(self) -> None:
        self.listing_ids = []
        self.conversation_ids = []
        self._bootstrap()

    def _bootstrap(self) -> None:
        if self.username and self.password and self._login():
            self._fetch_listing_ids()
            self._fetch_conversation_ids()

    def _login(self) -> bool:
        self.client.get("/auth/login/", name="auth.login.page")
        csrf_token = _extract_csrf_cookie(self)
        if not csrf_token:
            return False

        payload = {
            "email": self.email,
            "password": self.password,
            "csrfmiddlewaretoken": csrf_token,
        }
        headers = {"Referer": f"{self.host}/auth/login/"}
        with self.client.post(
            "/auth/login/",
            data=payload,
            headers=headers,
            allow_redirects=True,
            name="auth.login.submit",
            catch_response=True,
        ) as response:
            if response.status_code >= 400:
                response.failure(f"Login failed with {response.status_code}")
                return False
            response.success()

        if self._is_authenticated_session():
            return True

        # Student credentials are intentionally blocked from password login
        # in normal app flow, so for local debug/perf runs we fall back to
        # a dev-only login route keyed by username.
        self.client.get(
            f"/auth/dev-login/{quote(self.username, safe='')}/",
            allow_redirects=True,
            name="auth.dev_login",
        )
        return self._is_authenticated_session()

    def _is_authenticated_session(self) -> bool:
        response = self.client.get(
            "/auth/dashboard/",
            allow_redirects=False,
            name="auth.dashboard.check",
        )
        if response.status_code in (301, 302, 303, 307, 308):
            location = response.headers.get("Location", "")
            return "/auth/login/" not in location and "/accounts/login/" not in location
        return response.status_code == 200

    def _fetch_listing_ids(self) -> None:
        response = self.client.get("/student/find-housing/", name="student.find_housing.seed")
        if response.status_code == 200:
            self.listing_ids = _extract_listing_ids(response.text)

    def _fetch_conversation_ids(self) -> None:
        response = self.client.get("/chat/api/conversations/", name="chat.conversations.seed")
        if response.status_code != 200:
            return
        try:
            payload = response.json()
        except ValueError:
            self.conversation_ids = []
            return
        conversations = payload.get("conversations", [])
        self.conversation_ids = [
            int(conv["id"])
            for conv in conversations
            if isinstance(conv, dict) and conv.get("id") is not None
        ]

    def _csrf_headers(self, referer: str, json_body: bool = False) -> dict[str, str]:
        headers = {
            "Referer": referer,
            "X-CSRFToken": _extract_csrf_cookie(self),
        }
        if json_body:
            headers["Content-Type"] = "application/json"
        return headers

    def _random_listing_id(self) -> int | None:
        if not self.listing_ids:
            self._fetch_listing_ids()
        return random.choice(self.listing_ids) if self.listing_ids else None

    def _random_conversation_id(self) -> int | None:
        if not self.conversation_ids:
            self._fetch_conversation_ids()
        return random.choice(self.conversation_ids) if self.conversation_ids else None


class GuestVisitor(BasePerchUser):
    abstract = False
    weight = get_int_env("PERCH_LOCUST_GUEST_WEIGHT", 5)

    @task(3)
    def landing_page(self) -> None:
        self.client.get("/", name="guest.landing")

    @task(2)
    def login_page(self) -> None:
        self.client.get("/auth/login/", name="guest.login")

    @task(1)
    def signup_page(self) -> None:
        self.client.get("/auth/signup/", name="guest.signup")


class StudentBrowser(BasePerchUser):
    abstract = False
    weight = get_int_env("PERCH_LOCUST_STUDENT_BROWSER_WEIGHT", 45)

    def on_start(self) -> None:
        with student_cycle_lock:
            creds = next(student_credentials_cycle)
        self.username = creds["username"]
        self.password = creds["password"]
        self.email = creds.get("email", f"{self.username}@example.com")
        super().on_start()

    @task(4)
    def browse_housing(self) -> None:
        min_price = random.choice(["", "900", "1200", "1500"])
        max_price = random.choice(["", "2000", "2600", "3500"])
        bedrooms = random.choice(["", "1", "2", "3"])
        room_type = random.choice(["", "room", "whole_apartment"])
        self.client.get(
            "/student/find-housing/",
            params={
                "min_price": min_price,
                "max_price": max_price,
                "bedrooms": bedrooms,
                "room_type": room_type,
            },
            name="student.find_housing",
        )

    @task(3)
    def open_listing(self) -> None:
        listing_id = self._random_listing_id()
        if listing_id is None:
            return
        self.client.get(f"/listings/property/{listing_id}/", name="listing.property_detail")

    @task(2)
    def toggle_favorite(self) -> None:
        listing_id = self._random_listing_id()
        if listing_id is None:
            return
        headers = self._csrf_headers(f"{self.host}/student/find-housing/")
        self.client.post(
            f"/student/find-housing/{listing_id}/favorite/",
            data={
                "next": "/student/find-housing/",
                "csrfmiddlewaretoken": _extract_csrf_cookie(self),
            },
            headers=headers,
            name="listing.favorite_toggle",
        )

    @task(1)
    def submit_review(self) -> None:
        listing_id = self._random_listing_id()
        if listing_id is None:
            return
        headers = self._csrf_headers(f"{self.host}/listings/property/{listing_id}/")
        self.client.post(
            f"/listings/property/{listing_id}/review/",
            data={
                "stars": random.choice(["3", "4", "5"]),
                "csrfmiddlewaretoken": _extract_csrf_cookie(self),
            },
            headers=headers,
            name="listing.review_submit",
        )

    @task(1)
    def contact_realtor(self) -> None:
        listing_id = self._random_listing_id()
        if listing_id is None:
            return
        headers = self._csrf_headers(f"{self.host}/listings/property/{listing_id}/")
        self.client.post(
            f"/listings/property/{listing_id}/contact/",
            data={
                "message": "Hello, I am interested in this listing.",
                "csrfmiddlewaretoken": _extract_csrf_cookie(self),
            },
            headers=headers,
            name="listing.contact_realtor",
        )


class StudentMessenger(BasePerchUser):
    abstract = False
    weight = get_int_env("PERCH_LOCUST_STUDENT_MESSENGER_WEIGHT", 25)

    def on_start(self) -> None:
        with student_cycle_lock:
            creds = next(student_credentials_cycle)
        self.username = creds["username"]
        self.password = creds["password"]
        self.email = creds.get("email", f"{self.username}@example.com")
        super().on_start()

    @task(4)
    def list_conversations(self) -> None:
        self.client.get("/chat/api/conversations/", name="chat.conversations")

    @task(4)
    def fetch_messages(self) -> None:
        conv_id = self._random_conversation_id()
        if conv_id is None:
            return
        with self.client.get(
            f"/chat/api/conversations/{conv_id}/messages/",
            name="chat.messages",
            catch_response=True,
        ) as response:
            if response.status_code == 200:
                response.success()
            elif response.status_code in (403, 404):
                # Conversation visibility can change during load. Refresh once and retry.
                self._fetch_conversation_ids()
                retry_conv_id = self._random_conversation_id()
                if retry_conv_id is None:
                    response.failure("chat.messages rejected and no visible conversations remain")
                    return
                retry_response = self.client.get(
                    f"/chat/api/conversations/{retry_conv_id}/messages/",
                    name="chat.messages.retry",
                )
                if retry_response.status_code == 200:
                    response.success()
                else:
                    response.failure(
                        f"chat.messages rejected ({response.status_code}) and retry failed ({retry_response.status_code})"
                    )
            else:
                response.failure(f"chat.messages unexpected status {response.status_code}")

    @task(2)
    def search_chat_users(self) -> None:
        query = random.choice(["ma", "al", "br", "so", "ni", "te"])
        filter_type = random.choice(["all", "student", "lessor"])
        self.client.get(
            "/chat/api/users/search/",
            params={"q": query, "type": filter_type},
            name="chat.user_search",
        )

    @task(1)
    def create_or_update_conversation(self) -> None:
        response = self.client.get(
            "/chat/api/users/search/",
            params={"q": "te", "type": "all"},
            name="chat.user_search.seed",
        )
        if response.status_code != 200:
            return
        try:
            users = response.json().get("users", [])
        except ValueError:
            return
        target_ids = [item["id"] for item in users if item.get("id")]
        if not target_ids:
            return
        headers = self._csrf_headers(f"{self.host}/student/messages/", json_body=True)
        self.client.post(
            "/chat/api/conversations/create/",
            data=json.dumps({"user_ids": [random.choice(target_ids)], "name": ""}),
            headers=headers,
            name="chat.conversation_create",
        )


class StudentRoommateSeeker(BasePerchUser):
    abstract = False
    weight = get_int_env("PERCH_LOCUST_STUDENT_ROOMMATE_WEIGHT", 10)

    def on_start(self) -> None:
        with student_cycle_lock:
            creds = next(student_credentials_cycle)
        self.username = creds["username"]
        self.password = creds["password"]
        self.email = creds.get("email", f"{self.username}@example.com")
        super().on_start()

    @task(3)
    def roommates_page(self) -> None:
        self.client.get("/student/roommates/", name="student.roommates")

    @task(2)
    def profile_page(self) -> None:
        self.client.get("/student/profile/", name="student.profile_self")

    @task(1)
    def compatibility_page(self) -> None:
        self.client.get("/student/compatibility-survey/", name="student.compatibility")


class LessorManager(BasePerchUser):
    abstract = False
    weight = get_int_env("PERCH_LOCUST_LESSOR_WEIGHT", 15)

    def on_start(self) -> None:
        with lessor_cycle_lock:
            creds = next(lessor_credentials_cycle)
        self.username = creds["username"]
        self.password = creds["password"]
        self.email = creds.get("email", f"{self.username}@example.com")
        super().on_start()

    @task(4)
    def my_listings(self) -> None:
        self.client.get("/listings/", name="lessor.listings")

    @task(2)
    def create_listing_page(self) -> None:
        self.client.get("/listings/create/", name="lessor.listing_create_page")

    @task(2)
    def listing_detail(self) -> None:
        response = self.client.get("/listings/", name="lessor.listings.seed")
        listing_ids = [int(match) for match in OWNER_LISTING_ID_PATTERN.findall(response.text)]
        if not listing_ids:
            return
        self.client.get(f"/listings/{random.choice(listing_ids)}/", name="lessor.listing_detail")


class ChatWebSocketUser(StudentMessenger):
    abstract = False
    weight = 3 if get_int_env("PERCH_LOCUST_WS_ENABLED", 0) else 0

    @task(2)
    def websocket_chat_roundtrip(self) -> None:
        conv_id = self._random_conversation_id()
        if conv_id is None:
            return

        cookie_header = "; ".join(f"{k}={v}" for k, v in self.client.cookies.items())
        ws_scheme = "wss" if self.host.startswith("https://") else "ws"
        host_without_scheme = self.host.replace("https://", "").replace("http://", "")
        ws_url = f"{ws_scheme}://{host_without_scheme}/ws/chat/{conv_id}/"
        start = time.perf_counter()
        try:
            ws = WebSocket()
            ws.connect(ws_url, timeout=5, header=[f"Cookie: {cookie_header}"])
            payload = json.dumps({"message": "Locust websocket ping"})
            ws.send(payload)
            ws.recv()
            ws.close()
            elapsed = (time.perf_counter() - start) * 1000
            events.request.fire(
                request_type="WS",
                name="chat.websocket_roundtrip",
                response_time=elapsed,
                response_length=len(payload),
                exception=None,
                context={},
            )
        except WebSocketException as exc:
            elapsed = (time.perf_counter() - start) * 1000
            events.request.fire(
                request_type="WS",
                name="chat.websocket_roundtrip",
                response_time=elapsed,
                response_length=0,
                exception=exc,
                context={},
            )

