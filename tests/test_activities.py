import pytest
from fastapi.testclient import TestClient

from src.app import activities, app


@pytest.fixture
def client():
    return TestClient(app)


def test_root_redirects_to_static_index(client):
    response = client.get("/", follow_redirects=False)

    assert response.status_code == 307
    assert response.headers["location"] == "/static/index.html"


def test_get_activities_returns_activity_details(client):
    response = client.get("/activities")

    assert response.status_code == 200
    response_activities = response.json()
    assert set(response_activities) == set(activities)
    assert response_activities["Chess Club"] == activities["Chess Club"]


def test_signup_adds_participant(client):
    activity_name = "Art Club"
    email = "test-signup@mergington.edu"

    try:
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email},
        )

        assert response.status_code == 200
        assert response.json() == {
            "message": f"Signed up {email} for {activity_name}"
        }
        assert email in activities[activity_name]["participants"]
    finally:
        if email in activities[activity_name]["participants"]:
            activities[activity_name]["participants"].remove(email)


def test_signup_rejects_unknown_activity(client):
    response = client.post(
        "/activities/Unknown Club/signup",
        params={"email": "student@mergington.edu"},
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Activity not found"}


def test_signup_rejects_duplicate_participant(client):
    activity_name = "Chess Club"
    email = activities[activity_name]["participants"][0]

    response = client.post(
        f"/activities/{activity_name}/signup",
        params={"email": email},
    )

    assert response.status_code == 400
    assert response.json() == {"detail": "Already signed up"}


def test_signup_rejects_full_activity(client):
    activity_name = "Soccer Club"
    original_participants = activities[activity_name]["participants"][:]
    test_participants = [
        f"capacity-{index}@mergington.edu"
        for index in range(activities[activity_name]["max_participants"])
    ]
    activities[activity_name]["participants"] = test_participants[:]

    try:
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": "over-capacity@mergington.edu"},
        )

        assert response.status_code == 400
        assert response.json() == {"detail": "Activity is full"}
    finally:
        activities[activity_name]["participants"] = original_participants


def test_unregister_removes_participant(client):
    activity_name = "Drama Club"
    email = "test-unregister@mergington.edu"
    activities[activity_name]["participants"].append(email)

    try:
        response = client.delete(
            f"/activities/{activity_name}/signup",
            params={"email": email},
        )

        assert response.status_code == 200
        assert response.json() == {
            "message": f"Unregistered {email} from {activity_name}"
        }
        assert email not in activities[activity_name]["participants"]
    finally:
        if email in activities[activity_name]["participants"]:
            activities[activity_name]["participants"].remove(email)


def test_unregister_rejects_unknown_activity(client):
    response = client.delete(
        "/activities/Unknown Club/signup",
        params={"email": "student@mergington.edu"},
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Activity not found"}


def test_unregister_rejects_missing_participant(client):
    activity_name = "Science Club"
    email = "not-signed-up@mergington.edu"

    response = client.delete(
        f"/activities/{activity_name}/signup",
        params={"email": email},
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Student is not signed up"}
