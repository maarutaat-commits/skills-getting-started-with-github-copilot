"""
FastAPI tests for Mergington High School Activities API using AAA pattern.

AAA Pattern:
- Arrange: Set up test data and test client
- Act: Execute the endpoint being tested
- Assert: Verify the response and state changes
"""

import pytest
from fastapi.testclient import TestClient
from src.app import app


@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    return TestClient(app)


class TestGetActivities:
    """Tests for GET /activities endpoint."""

    def test_get_activities_returns_all_activities(self, client):
        """Arrange: N/A (no setup needed)
        Act: Make GET request to /activities
        Assert: Verify response contains all 9 activities with correct structure"""
        
        response = client.get("/activities")
        
        assert response.status_code == 200
        activities = response.json()
        assert len(activities) == 9
        assert "Chess Club" in activities
        assert "Programming Class" in activities
        assert all("description" in act for act in activities.values())
        assert all("schedule" in act for act in activities.values())
        assert all("max_participants" in act for act in activities.values())
        assert all("participants" in act for act in activities.values())

    def test_get_activities_chess_club_has_participants(self, client):
        """Arrange: N/A
        Act: Get activities
        Assert: Verify Chess Club has expected participants"""
        
        response = client.get("/activities")
        activities = response.json()
        chess_club = activities["Chess Club"]
        
        assert "michael@mergington.edu" in chess_club["participants"]
        assert "daniel@mergington.edu" in chess_club["participants"]
        assert len(chess_club["participants"]) == 2


class TestSignupForActivity:
    """Tests for POST /activities/{activity_name}/signup endpoint."""

    def test_signup_success(self, client):
        """Arrange: Get initial activity state
        Act: Sign up a new student for an activity with available spots
        Assert: Verify success response and participant is added"""
        
        # Arrange
        activity_name = "Tennis Team"
        email = "newstudent@mergington.edu"
        
        # Act
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        
        # Assert
        assert response.status_code == 200
        assert response.json()["message"] == f"Signed up {email} for {activity_name}"
        
        # Verify participant was added
        activities = client.get("/activities").json()
        assert email in activities[activity_name]["participants"]

    def test_signup_invalid_activity(self, client):
        """Arrange: Use non-existent activity name
        Act: Try to sign up for activity that doesn't exist
        Assert: Verify 404 error response"""
        
        # Arrange
        activity_name = "Nonexistent Activity"
        email = "student@mergington.edu"
        
        # Act
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        
        # Assert
        assert response.status_code == 404
        assert response.json()["detail"] == "Activity not found"

    def test_signup_duplicate_email(self, client):
        """Arrange: Use email already registered for an activity
        Act: Try to sign up same email again for same activity
        Assert: Verify 400 error response"""
        
        # Arrange
        activity_name = "Chess Club"
        email = "michael@mergington.edu"  # Already signed up
        
        # Act
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        
        # Assert
        assert response.status_code == 400
        assert response.json()["detail"] == "Student already signed up for this activity"

    def test_signup_same_email_different_activity(self, client):
        """Arrange: Sign up student for one activity, then try another
        Act: Sign up same email for different activity
        Assert: Verify success (same email can register for multiple activities)"""
        
        # Arrange
        email = "testmulti@mergington.edu"
        activity1 = "Tennis Team"
        activity2 = "Art Club"
        
        # Act - Sign up for first activity
        response1 = client.post(
            f"/activities/{activity1}/signup",
            params={"email": email}
        )
        
        # Act - Sign up for second activity
        response2 = client.post(
            f"/activities/{activity2}/signup",
            params={"email": email}
        )
        
        # Assert
        assert response1.status_code == 200
        assert response2.status_code == 200
        activities = client.get("/activities").json()
        assert email in activities[activity1]["participants"]
        assert email in activities[activity2]["participants"]


class TestUnregisterFromActivity:
    """Tests for DELETE /activities/{activity_name}/unregister endpoint."""

    def test_unregister_success(self, client):
        """Arrange: First sign up a student, then unregister them
        Act: Delete the student from activity
        Assert: Verify success and participant is removed"""
        
        # Arrange
        activity_name = "Basketball Team"
        email = "tempstudent@mergington.edu"
        client.post(f"/activities/{activity_name}/signup", params={"email": email})
        
        # Act
        response = client.delete(
            f"/activities/{activity_name}/unregister",
            params={"email": email}
        )
        
        # Assert
        assert response.status_code == 200
        assert response.json()["message"] == f"Unregistered {email} from {activity_name}"
        
        # Verify participant was removed
        activities = client.get("/activities").json()
        assert email not in activities[activity_name]["participants"]

    def test_unregister_invalid_activity(self, client):
        """Arrange: Use non-existent activity name
        Act: Try to unregister from activity that doesn't exist
        Assert: Verify 404 error response"""
        
        # Arrange
        activity_name = "Fake Activity"
        email = "student@mergington.edu"
        
        # Act
        response = client.delete(
            f"/activities/{activity_name}/unregister",
            params={"email": email}
        )
        
        # Assert
        assert response.status_code == 404
        assert response.json()["detail"] == "Activity not found"

    def test_unregister_not_registered(self, client):
        """Arrange: Use email not registered for activity
        Act: Try to unregister student who isn't signed up
        Assert: Verify 400 error response"""
        
        # Arrange
        activity_name = "Debate Club"
        email = "notreg@mergington.edu"
        
        # Act
        response = client.delete(
            f"/activities/{activity_name}/unregister",
            params={"email": email}
        )
        
        # Assert
        assert response.status_code == 400
        assert response.json()["detail"] == "Student is not registered for this activity"

    def test_unregister_existing_participant(self, client):
        """Arrange: Use email that's already in an activity
        Act: Unregister an existing participant
        Assert: Verify success and participant count decreases"""
        
        # Arrange
        activity_name = "Chess Club"
        email = "michael@mergington.edu"
        activities_before = client.get("/activities").json()
        initial_count = len(activities_before[activity_name]["participants"])
        
        # Act
        response = client.delete(
            f"/activities/{activity_name}/unregister",
            params={"email": email}
        )
        
        # Assert
        assert response.status_code == 200
        activities_after = client.get("/activities").json()
        final_count = len(activities_after[activity_name]["participants"])
        assert final_count == initial_count - 1
        assert email not in activities_after[activity_name]["participants"]


class TestSignupUnregisterWorkflow:
    """Integration tests for signup and unregister workflow."""

    def test_signup_then_unregister_workflow(self, client):
        """Arrange: Set up a complete workflow
        Act: Sign up new student, verify they appear, then unregister
        Assert: Verify full workflow works correctly"""
        
        # Arrange
        activity_name = "Science Club"
        email = "workflow@mergington.edu"
        
        # Act 1: Sign up
        signup_response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        
        # Assert 1: Signup successful
        assert signup_response.status_code == 200
        activities = client.get("/activities").json()
        assert email in activities[activity_name]["participants"]
        
        # Act 2: Unregister
        unregister_response = client.delete(
            f"/activities/{activity_name}/unregister",
            params={"email": email}
        )
        
        # Assert 2: Unregister successful
        assert unregister_response.status_code == 200
        activities = client.get("/activities").json()
        assert email not in activities[activity_name]["participants"]

    def test_signup_twice_then_unregister(self, client):
        """Arrange: Try to sign up twice
        Act: First signup succeeds, second fails, then unregister
        Assert: Verify error on duplicate, and unregister works on original"""
        
        # Arrange
        activity_name = "Music Ensemble"
        email = "duplicate@mergington.edu"
        
        # Act 1: First signup
        response1 = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        
        # Assert 1
        assert response1.status_code == 200
        
        # Act 2: Second signup (should fail)
        response2 = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        
        # Assert 2
        assert response2.status_code == 400
        assert "already signed up" in response2.json()["detail"]
        
        # Act 3: Unregister
        response3 = client.delete(
            f"/activities/{activity_name}/unregister",
            params={"email": email}
        )
        
        # Assert 3
        assert response3.status_code == 200
