"""
AstroDat Load Test Suite
========================
Realistic, multi-persona Locust load test for the AstroDat observation platform.

Personas modeled:
  1. AnonymousBrowser    (60%) – Unauthenticated visitors who browse, search, paginate.
  2. ActiveObserver      (25%) – Logged-in power users who add observations, search, paginate, manage profile.
  3. NewUserJourney      (10%) – Full signup → login → first observation → profile check → logout lifecycle.
  4. AdminSpike           (5%) – Authenticated users who hammer write/delete paths for stress testing.

Run:
    locust -f locustfile.py --host http://localhost:5000
    locust -f locustfile.py --host http://localhost:5000 --headless -u 200 -r 20 -t 5m
"""

import os
import re
import random
import string
import logging
from locust import HttpUser, task, between, tag, events, SequentialTaskSet

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

# Pre-seeded test accounts (must exist in the DB or FLASK_ENV_TESTING=TRUE)
TEST_ACCOUNTS = [
    {"username": "test_user_64345", "password": "SecurePassword123!"},
    {"username": "test_user_76813", "password": "SecurePassword123!"},
    {"username": "test_user_58505", "password": "SecurePassword123!"},
]

# Realistic astronomical catalog prefixes and object types (from seed_db.py)
CATALOG_PREFIXES = [
    "Messier", "M", "NGC", "IC", "C", "Caldwell", "Herschel", "Sh2",
    "RCW", "Gum", "vdb", "Barnard", "B", "Abell", "Arp", "VV", "HCG",
    "UGC", "PGC", "MCG", "ESO", "Zwicky", "CGCG", "Markarian", "Mrk",
]

OBJECT_TYPES = [
    "Emission Nebula", "Reflection Nebula", "Dark Nebula", "Planetary Nebula",
    "Supernova Remnant", "H II Region", "Star Cluster", "Open Cluster",
    "Globular Cluster", "Galaxy", "Spiral Galaxy", "Elliptical Galaxy",
    "Irregular Galaxy", "Dwarf Galaxy", "Quasar", "Exoplanet",
    "Hot Jupiter", "Super-Earth", "Protoplanetary Disk", "Asteroid",
    "Comet", "Neutron Star", "Pulsar", "Black Hole", "White Dwarf",
]

SEARCH_QUERIES = [
    "Messier", "NGC", "M", "Orion", "Andromeda", "Mars", "M45", "IC",
    "Nebula", "Star", "Galaxy", "Exoplanet", "Caldwell", "Abell",
    "Barnard", "Spiral", "Pulsar", "Quasar", "Comet", "Asteroid",
]

OBSERVATION_NOTES = [
    "Clear skies, excellent visibility.",
    "Slight light pollution from the city.",
    "Used a 10-inch Dobsonian telescope.",
    "Observation during new moon.",
    "Very faint, required averted vision.",
    "Captured with 30s exposure on CMOS sensor.",
    "First light with new equatorial mount.",
    "Confirmed visual binary at 150x magnification.",
    "Bortle 3 sky, transparency 4/5, seeing 3/5.",
    "Sketch made at the eyepiece, 200x magnification.",
    "",
]

logger = logging.getLogger("astrodat-loadtest")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def generate_realistic_target_name():
    """Generate a target name matching the app's seed data format."""
    prefix = random.choice(CATALOG_PREFIXES)
    catalog_num = random.randint(1, 8000)
    obj_type = random.choice(OBJECT_TYPES)
    return f"{prefix} {catalog_num} {obj_type}"


def generate_valid_ra():
    """Generate a valid Right Ascension string (HH MM SS)."""
    h = random.randint(0, 23)
    m = random.randint(0, 59)
    s = random.randint(0, 59)
    return f"{h:02d}h {m:02d}m {s:02d}s"


def generate_valid_dec():
    """Generate a valid Declination string (±DD° MM' SS'')."""
    sign = random.choice(["+", "-"])
    d = random.randint(0, 89)
    m = random.randint(0, 59)
    s = random.randint(0, 59)
    return f"{sign}{d:02d}° {m:02d}' {s:02d}''"


def extract_observation_id(html_fragment):
    """
    Parse the target_row.html fragment returned by POST /add-target
    to extract the observation ID for later deletion.
    Looks for patterns like id="target-row-123" or delete-target/123.
    """
    # Try to find the ID from the delete endpoint URL pattern
    match = re.search(r'/delete-target/(\d+)', html_fragment)
    if match:
        return int(match.group(1))
    # Fallback: look for a data attribute or row id
    match = re.search(r'id=["\']target-row-(\d+)["\']', html_fragment)
    if match:
        return int(match.group(1))
    return None


def _login(client, username, password):
    """Shared login helper. Returns True on success."""
    with client.post(
        "/login-process",
        data={"username": username, "password": password},
        name="/login-process",
        catch_response=True,
    ) as resp:
        if resp.status_code == 200:
            # Success is indicated by HX-Redirect header or "OK" body
            if resp.headers.get("HX-Redirect") == "/" or resp.text.strip() == "OK":
                resp.success()
                return True
            # Any 200 with an error message body means auth failure
            if "Invalid" in resp.text or "not found" in resp.text.lower():
                resp.failure(f"Auth failed: {resp.text[:80]}")
                return False
            # Ambiguous 200 — still treat as success for test users
            resp.success()
            return True
        resp.failure(f"Login returned {resp.status_code}")
        return False


# ---------------------------------------------------------------------------
# Persona 1: Anonymous Browser (60% of traffic)
# ---------------------------------------------------------------------------

class AnonymousBrowser(HttpUser):
    """
    Unauthenticated visitor who browses the dashboard, searches,
    paginates, and occasionally views the login/signup pages.
    Represents the majority of real-world traffic.
    """
    weight = 60
    wait_time = between(1.0, 5.0)

    @tag("read", "dashboard")
    @task(10)
    def view_dashboard(self):
        """Land on the homepage — the single most common request."""
        with self.client.get("/", name="/", catch_response=True) as resp:
            if resp.status_code != 200:
                resp.failure(f"Dashboard returned {resp.status_code}")

    @tag("read", "search")
    @task(6)
    def search_targets(self):
        """Search with a realistic query string."""
        query = random.choice(SEARCH_QUERIES)
        with self.client.get(
            f"/search?q={query}&page=0",
            name="/search?q=[query]",
            catch_response=True,
        ) as resp:
            if resp.status_code != 200:
                resp.failure(f"Search returned {resp.status_code}")

    @tag("read", "search")
    @task(3)
    def search_empty_query(self):
        """Search with an empty query — returns recent observations."""
        with self.client.get(
            "/search?q=&page=0",
            name="/search?q=&page=0",
            catch_response=True,
        ) as resp:
            if resp.status_code != 200:
                resp.failure(f"Empty search returned {resp.status_code}")

    @tag("read", "pagination")
    @task(4)
    def paginate_load_more(self):
        """Simulate scrolling and loading more results (pages 1–5)."""
        page = random.randint(1, 5)
        with self.client.get(
            f"/load-more?page={page}",
            name="/load-more?page=[n]",
            catch_response=True,
        ) as resp:
            if resp.status_code != 200:
                resp.failure(f"Load-more returned {resp.status_code}")

    @tag("read", "pagination")
    @task(2)
    def paginated_search(self):
        """Search with pagination — user typed a query then scrolled."""
        query = random.choice(SEARCH_QUERIES)
        page = random.randint(1, 3)
        with self.client.get(
            f"/search?q={query}&page={page}",
            name="/search?q=[query]&page=[n]",
            catch_response=True,
        ) as resp:
            if resp.status_code != 200:
                resp.failure(f"Paginated search returned {resp.status_code}")

    @tag("read", "auth")
    @task(2)
    def view_login_page(self):
        """Visitor considers logging in."""
        self.client.get("/login", name="/login")

    @tag("read", "auth")
    @task(1)
    def view_signup_page(self):
        """Visitor considers signing up."""
        self.client.get("/signup", name="/signup")

    @tag("read", "search")
    @task(1)
    def search_long_query_rejected(self):
        """Edge case: query exceeding the 40 character limit."""
        long_query = "A" * 45
        with self.client.get(
            f"/search?q={long_query}&page=0",
            name="/search?q=[too-long]",
            catch_response=True,
        ) as resp:
            if resp.status_code == 200 and "too long" in resp.text.lower():
                resp.success()
            elif resp.status_code == 200:
                resp.success()  # Acceptable — server handled it
            else:
                resp.failure(f"Long query returned {resp.status_code}")


# ---------------------------------------------------------------------------
# Persona 2: Active Observer (25% of traffic)
# ---------------------------------------------------------------------------

class ActiveObserver(HttpUser):
    """
    A logged-in power user who primarily reads the dashboard and searches,
    but also adds observations, views their profile, and adjusts settings.
    Logs in once on start, stays authenticated for the session duration.
    """
    weight = 25
    wait_time = between(2.0, 6.0)

    created_target_ids: list  # Track IDs for realistic cleanup

    def on_start(self):
        """Authenticate with a pre-seeded test account."""
        self.created_target_ids = []
        creds = random.choice(TEST_ACCOUNTS)
        self.username = creds["username"]
        success = _login(self.client, creds["username"], creds["password"])
        if not success:
            logger.warning(f"ActiveObserver failed to login as {creds['username']}")

    def on_stop(self):
        """Clean up: delete any observations created during this session."""
        for tid in self.created_target_ids:
            self.client.delete(
                f"/delete-target/{tid}",
                name="/delete-target/[id] (cleanup)",
            )
        self.created_target_ids.clear()

    @tag("read", "dashboard")
    @task(10)
    def view_dashboard(self):
        with self.client.get("/", name="/", catch_response=True) as resp:
            if resp.status_code != 200:
                resp.failure(f"Dashboard returned {resp.status_code}")

    @tag("read", "search")
    @task(7)
    def search_targets(self):
        query = random.choice(SEARCH_QUERIES)
        self.client.get(f"/search?q={query}&page=0", name="/search?q=[query]")

    @tag("read", "pagination")
    @task(4)
    def paginate(self):
        page = random.randint(1, 5)
        self.client.get(f"/load-more?page={page}", name="/load-more?page=[n]")

    @tag("write", "observation")
    @task(3)
    def add_observation(self):
        """Add a new observation with realistic astronomical data."""
        payload = {
            "name": generate_realistic_target_name(),
            "ra": generate_valid_ra(),
            "dec": generate_valid_dec(),
            "notes": random.choice(OBSERVATION_NOTES),
        }
        with self.client.post(
            "/add-target",
            data=payload,
            name="/add-target",
            catch_response=True,
        ) as resp:
            if resp.status_code == 200 and resp.text.strip():
                obs_id = extract_observation_id(resp.text)
                if obs_id:
                    self.created_target_ids.append(obs_id)
                resp.success()
            elif resp.status_code == 400:
                # Expected if validation fails — still a valid test
                resp.success()
            else:
                resp.failure(f"Add-target returned {resp.status_code}: {resp.text[:100]}")

    @tag("write", "observation")
    @task(1)
    def delete_own_observation(self):
        """Delete a previously created observation (if any exist)."""
        if not self.created_target_ids:
            return
        tid = self.created_target_ids.pop(random.randrange(len(self.created_target_ids)))
        with self.client.delete(
            f"/delete-target/{tid}",
            name="/delete-target/[id]",
            catch_response=True,
        ) as resp:
            if resp.status_code in (200, 404):
                resp.success()
            else:
                resp.failure(f"Delete returned {resp.status_code}")

    @tag("read", "profile")
    @task(2)
    def view_profile(self):
        with self.client.get("/profile", name="/profile", catch_response=True) as resp:
            if resp.status_code != 200:
                resp.failure(f"Profile returned {resp.status_code}")

    @tag("read", "settings")
    @task(1)
    def view_and_save_settings(self):
        """Simulate opening settings and saving (no actual change)."""
        self.client.get("/settings", name="/settings")
        self.client.post("/settings_saving_process", name="/settings_saving_process")

    @tag("write", "observation")
    @task(1)
    def add_observation_missing_name(self):
        """Edge case: submit with a missing target name → expect 400."""
        payload = {
            "name": "",
            "ra": generate_valid_ra(),
            "dec": generate_valid_dec(),
            "notes": "Should be rejected.",
        }
        with self.client.post(
            "/add-target",
            data=payload,
            name="/add-target (no name)",
            catch_response=True,
        ) as resp:
            if resp.status_code == 400:
                resp.success()  # Expected validation error
            else:
                resp.failure(f"Expected 400, got {resp.status_code}")

    @tag("write", "observation")
    @task(1)
    def add_observation_bad_coordinates(self):
        """Edge case: invalid RA/Dec values → expect 400 from coordinate validation."""
        payload = {
            "name": generate_realistic_target_name(),
            "ra": "99h 99m 99s",   # Invalid: hours > 23, mins/secs > 59
            "dec": "+99° 99' 99''", # Invalid: degrees > 90
            "notes": "Bad coordinates test.",
        }
        with self.client.post(
            "/add-target",
            data=payload,
            name="/add-target (bad coords)",
            catch_response=True,
        ) as resp:
            if resp.status_code == 400:
                resp.success()  # Expected validation error
            else:
                resp.failure(f"Expected 400 for bad coords, got {resp.status_code}")


# ---------------------------------------------------------------------------
# Persona 3: New User Journey (10% of traffic) — Sequential lifecycle
# ---------------------------------------------------------------------------

class SignupLoginWorkflow(SequentialTaskSet):
    """
    Models the complete new-user funnel:
    signup page → register → login page → authenticate → browse → add obs → profile → logout.
    """

    def on_start(self):
        rand_suffix = "".join(random.choices(string.ascii_lowercase + string.digits, k=8))
        self.username = f"locust_{rand_suffix}"
        self.password = "TestPass1234!"
        self.created_target_ids = []

    # Step 1: View signup page
    @task
    def step_view_signup(self):
        self.client.get("/signup", name="/signup (journey)")

    # Step 2: Register
    @task
    def step_register(self):
        with self.client.post(
            "/signup-process",
            data={"username": self.username, "password": self.password},
            name="/signup-process (journey)",
            catch_response=True,
        ) as resp:
            if resp.status_code == 201:
                resp.success()
            elif resp.status_code == 200 and "Created" in resp.text:
                resp.success()
            elif "already taken" in resp.text.lower():
                resp.success()  # Race condition — acceptable
            else:
                resp.failure(f"Signup failed: {resp.status_code} — {resp.text[:100]}")

    # Step 3: View login page
    @task
    def step_view_login(self):
        self.client.get("/login", name="/login (journey)")

    # Step 4: Authenticate
    @task
    def step_login(self):
        success = _login(self.client, self.username, self.password)
        if not success:
            logger.warning(f"Journey user {self.username} failed to login")

    # Step 5: Browse dashboard
    @task
    def step_browse_dashboard(self):
        self.client.get("/", name="/ (journey)")

    # Step 6: Search for something
    @task
    def step_search(self):
        query = random.choice(SEARCH_QUERIES)
        self.client.get(f"/search?q={query}&page=0", name="/search (journey)")

    # Step 7: Load more results
    @task
    def step_load_more(self):
        self.client.get("/load-more?page=1", name="/load-more (journey)")

    # Step 8: Add first observation
    @task
    def step_add_first_observation(self):
        payload = {
            "name": generate_realistic_target_name(),
            "ra": generate_valid_ra(),
            "dec": generate_valid_dec(),
            "notes": "My first observation! 🔭",
        }
        with self.client.post(
            "/add-target",
            data=payload,
            name="/add-target (journey)",
            catch_response=True,
        ) as resp:
            if resp.status_code == 200:
                obs_id = extract_observation_id(resp.text)
                if obs_id:
                    self.created_target_ids.append(obs_id)
                resp.success()

    # Step 9: Check profile
    @task
    def step_view_profile(self):
        self.client.get("/profile", name="/profile (journey)")

    # Step 10: View settings
    @task
    def step_view_settings(self):
        self.client.get("/settings", name="/settings (journey)")

    # Step 11: Logout and end lifecycle
    @task
    def step_logout(self):
        # Clean up created observations before logging out
        for tid in self.created_target_ids:
            self.client.delete(
                f"/delete-target/{tid}",
                name="/delete-target/[id] (journey cleanup)",
            )
        self.created_target_ids.clear()

        self.client.get("/logout", name="/logout (journey)")
        self.interrupt()  # End this sequential workflow; Locust will restart it


class NewUserJourney(HttpUser):
    """Wraps the sequential signup-to-logout workflow."""
    weight = 10
    wait_time = between(1.5, 4.0)
    tasks = [SignupLoginWorkflow]


# ---------------------------------------------------------------------------
# Persona 4: Admin / Stress Spike (5% of traffic)
# ---------------------------------------------------------------------------

class AdminSpike(HttpUser):
    """
    Authenticated user that aggressively writes and deletes observations
    to stress-test the database write path, WAL journaling, and busy_timeout.
    Also hits delete on non-existent IDs to test 404 handling.
    """
    weight = 5
    wait_time = between(0.5, 2.0)  # Much faster than normal users

    created_target_ids: list

    def on_start(self):
        self.created_target_ids = []
        creds = random.choice(TEST_ACCOUNTS)
        _login(self.client, creds["username"], creds["password"])

    def on_stop(self):
        for tid in self.created_target_ids:
            self.client.delete(
                f"/delete-target/{tid}",
                name="/delete-target/[id] (spike cleanup)",
            )
        self.created_target_ids.clear()

    @tag("write", "stress")
    @task(5)
    def rapid_add_observation(self):
        """Rapid-fire observation creation."""
        payload = {
            "name": generate_realistic_target_name(),
            "ra": generate_valid_ra(),
            "dec": generate_valid_dec(),
            "notes": f"Spike test #{random.randint(1, 99999)}",
        }
        with self.client.post(
            "/add-target",
            data=payload,
            name="/add-target (spike)",
            catch_response=True,
        ) as resp:
            if resp.status_code == 200:
                obs_id = extract_observation_id(resp.text)
                if obs_id:
                    self.created_target_ids.append(obs_id)
                resp.success()

    @tag("write", "stress")
    @task(3)
    def delete_created_observation(self):
        """Delete a previously created observation."""
        if not self.created_target_ids:
            return
        tid = self.created_target_ids.pop(random.randrange(len(self.created_target_ids)))
        with self.client.delete(
            f"/delete-target/{tid}",
            name="/delete-target/[id] (spike)",
            catch_response=True,
        ) as resp:
            if resp.status_code in (200, 404):
                resp.success()

    @tag("write", "stress")
    @task(1)
    def delete_nonexistent_target(self):
        """Hit DELETE on a non-existent ID — should return 404 gracefully."""
        fake_id = random.randint(900_000_000, 999_999_999)
        with self.client.delete(
            f"/delete-target/{fake_id}",
            name="/delete-target/[nonexistent]",
            catch_response=True,
        ) as resp:
            if resp.status_code == 404:
                resp.success()
            elif resp.status_code == 200:
                resp.success()  # ID happened to exist — fine
            else:
                resp.failure(f"Expected 404, got {resp.status_code}")

    @tag("read", "dashboard")
    @task(2)
    def view_dashboard(self):
        self.client.get("/", name="/ (spike)")

    @tag("read", "search")
    @task(2)
    def rapid_search(self):
        query = random.choice(SEARCH_QUERIES)
        self.client.get(f"/search?q={query}&page=0", name="/search (spike)")

    @tag("read", "profile")
    @task(1)
    def view_profile(self):
        self.client.get("/profile", name="/profile (spike)")


# ---------------------------------------------------------------------------
# Event Hooks — Test-level logging and stats
# ---------------------------------------------------------------------------

@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """Log test configuration at startup."""
    testing_env = os.environ.get("FLASK_ENV_TESTING", "not set")
    logger.info("=" * 60)
    logger.info("AstroDat Load Test Starting")
    logger.info(f"  Target host      : {environment.host}")
    logger.info(f"  FLASK_ENV_TESTING: {testing_env}")
    logger.info(f"  User weights     : Anonymous=60, Observer=25, NewUser=10, Spike=5")
    logger.info("=" * 60)
    if testing_env != "TRUE":
        logger.warning(
            "FLASK_ENV_TESTING is not 'TRUE'. "
            "Test accounts may fail to authenticate against real bcrypt hashes. "
            "Set FLASK_ENV_TESTING=TRUE for load testing with pre-seeded users."
        )


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    logger.info("=" * 60)
    logger.info("AstroDat Load Test Complete")
    logger.info("=" * 60)