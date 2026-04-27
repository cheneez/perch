import os
import time

from locust import LoadTestShape, events

try:
    from .config import get_profile
    from .users import (
        ChatWebSocketUser,
        GuestVisitor,
        LessorManager,
        StudentBrowser,
        StudentMessenger,
        StudentRoommateSeeker,
    )
except ImportError:
    # Locust loads -f files as standalone modules, so relative imports
    # are unavailable in that execution mode.
    from config import get_profile
    from users import (
        ChatWebSocketUser,
        GuestVisitor,
        LessorManager,
        StudentBrowser,
        StudentMessenger,
        StudentRoommateSeeker,
    )


USE_SHAPE = os.getenv("PERCH_LOCUST_USE_SHAPE", "0").lower() in ("1", "true", "yes")


if USE_SHAPE:
    class PerchProfileShape(LoadTestShape):
        profile = get_profile()

        def tick(self):
            run_time = self.get_run_time()
            if run_time > self.profile.run_minutes * 60:
                return None
            return self.profile.users, self.profile.spawn_rate


@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    environment.stats.reset_all()
    if USE_SHAPE:
        profile = get_profile()
        print(
            "Perch Locust profile started "
            f"(users={profile.users}, spawn_rate={profile.spawn_rate}, minutes={profile.run_minutes})"
        )
    else:
        print("Perch Locust started with UI/manual user controls.")


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    stats = environment.stats.total
    fail_ratio = stats.fail_ratio
    p95 = stats.get_response_time_percentile(0.95)
    p99 = stats.get_response_time_percentile(0.99)
    print("Perch load test summary")
    print(f"- requests: {stats.num_requests}")
    print(f"- fail ratio: {fail_ratio:.4f}")
    print(f"- p95: {p95:.2f}ms")
    print(f"- p99: {p99:.2f}ms")

    slo_failures = []
    if fail_ratio > 0.01:
        slo_failures.append("overall fail ratio > 1%")
    if p95 > 800:
        slo_failures.append("p95 > 800ms")
    if p99 > 1200:
        slo_failures.append("p99 > 1200ms")

    if slo_failures:
        print(f"- SLO status: FAIL ({', '.join(slo_failures)})")
    else:
        print("- SLO status: PASS")

