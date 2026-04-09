"""
Tests for the High School Management System API

Uses pytest and FastAPI TestClient with Arrange-Act-Assert structure.
"""

from copy import deepcopy
from urllib.parse import quote

import pytest
from fastapi.testclient import TestClient

from src.app import app, activities

INITIAL_ACTIVITIES = deepcopy(activities)


@pytest.fixture(autouse=True)
def reset_activities():
    """Reset the in-memory activities data before each test."""
    activities.clear()
    activities.update(deepcopy(INITIAL_ACTIVITIES))
    yield
    activities.clear()
    activities.update(deepcopy(INITIAL_ACTIVITIES))


@pytest.fixture
def client():
    """Provide a TestClient for the FastAPI application."""
    return TestClient(app)


class TestGetActivities:
    def test_get_all_activities(self, client):
        # Arrange: initial activities are already loaded

        # Act
        response = client.get("/activities")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "Chess Club" in data
        assert "Programming Class" in data
        assert isinstance(data["Chess Club"]["participants"], list)

    def test_activity_structure_contains_required_fields(self, client):
        # Arrange: no additional setup

        # Act
        response = client.get("/activities")
        data = response.json()

        # Assert
        required_fields = ["description", "schedule", "max_participants", "participants"]
        for activity_name, activity_data in data.items():
            for field in required_fields:
                assert field in activity_data
            assert isinstance(activity_data["participants"], list)


class TestSignupForActivity:
    def test_signup_new_student_success(self, client):
        # Arrange
        activity_name = "Chess Club"
        email = "newstudent@mergington.edu"

        # Act
        response = client.post(
            f"/activities/{quote(activity_name)}/signup",
            params={"email": email},
        )

        # Assert
        assert response.status_code == 200
        assert response.json()["message"] == f"Signed up {email} for {activity_name}"
        assert email in activities[activity_name]["participants"]

    def test_signup_duplicate_student_returns_400(self, client):
        # Arrange
        activity_name = "Chess Club"
        email = "michael@mergington.edu"

        # Act
        response = client.post(
            f"/activities/{quote(activity_name)}/signup",
            params={"email": email},
        )

        # Assert
        assert response.status_code == 400
        assert response.json()["detail"] == "Student already signed up for this activity"

    def test_signup_nonexistent_activity_returns_404(self, client):
        # Arrange
        activity_name = "Nonexistent Activity"
        email = "student@mergington.edu"

        # Act
        response = client.post(
            f"/activities/{quote(activity_name)}/signup",
            params={"email": email},
        )

        # Assert
        assert response.status_code == 404
        assert response.json()["detail"] == "Activity not found"


class TestRemoveParticipant:
    def test_remove_existing_participant_success(self, client):
        # Arrange
        activity_name = "Chess Club"
        email = "newparticipant@mergington.edu"
        client.post(
            f"/activities/{quote(activity_name)}/signup",
            params={"email": email},
        )

        # Act
        response = client.delete(
            f"/activities/{quote(activity_name)}/participants",
            params={"email": email},
        )

        # Assert
        assert response.status_code == 200
        assert response.json()["message"] == f"Removed {email} from {activity_name}"
        assert email not in activities[activity_name]["participants"]

    def test_remove_missing_participant_returns_404(self, client):
        # Arrange
        activity_name = "Chess Club"
        email = "absent@mergington.edu"

        # Act
        response = client.delete(
            f"/activities/{quote(activity_name)}/participants",
            params={"email": email},
        )

        # Assert
        assert response.status_code == 404
        assert response.json()["detail"] == "Participant not registered for this activity"
