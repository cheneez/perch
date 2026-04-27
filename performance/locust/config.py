import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Profile:
    users: int
    spawn_rate: int
    run_minutes: int


PROFILES = {
    "local_smoke": Profile(users=25, spawn_rate=5, run_minutes=10),
    "local_baseline": Profile(users=100, spawn_rate=10, run_minutes=20),
    "staging_baseline": Profile(users=200, spawn_rate=15, run_minutes=45),
    "staging_sustained": Profile(users=300, spawn_rate=10, run_minutes=60),
}


def get_profile() -> Profile:
    profile_name = os.getenv("PERCH_LOCUST_PROFILE", "local_baseline")
    return PROFILES.get(profile_name, PROFILES["local_baseline"])


def get_int_env(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, str(default)))
    except ValueError:
        return default

