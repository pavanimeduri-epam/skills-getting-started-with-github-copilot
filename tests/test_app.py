from urllib.parse import quote


def test_root_redirects_to_static_index(client):
    # Arrange
    expected_location = "/static/index.html"

    # Act
    response = client.get("/", follow_redirects=False)

    # Assert
    assert response.status_code == 307
    assert response.headers["location"] == expected_location


def test_get_activities_returns_activity_details(client):
    # Arrange
    expected_fields = {"description", "schedule", "max_participants", "participants"}

    # Act
    response = client.get("/activities")

    # Assert
    assert response.status_code == 200
    activities = response.json()
    assert "Chess Club" in activities
    for activity in activities.values():
        assert set(activity) == expected_fields
        assert isinstance(activity["participants"], list)


def test_signup_adds_participant_to_activity(client):
    # Arrange
    activity_name = "Chess Club"
    email = "new.student@mergington.edu"
    encoded_activity = quote(activity_name, safe="")

    # Act
    response = client.post(f"/activities/{encoded_activity}/signup", params={"email": email})

    # Assert
    assert response.status_code == 200
    assert response.json() == {"message": f"Signed up {email} for {activity_name}"}
    assert email in client.get("/activities").json()[activity_name]["participants"]


def test_signup_rejects_duplicate_participant(client):
    # Arrange
    activity_name = "Chess Club"
    email = "michael@mergington.edu"
    original_count = len(client.get("/activities").json()[activity_name]["participants"])

    # Act
    response = client.post(f"/activities/{quote(activity_name, safe='')}/signup", params={"email": email})

    # Assert
    assert response.status_code == 400
    assert response.json() == {"detail": "Student is already signed up for this activity"}
    participants = client.get("/activities").json()[activity_name]["participants"]
    assert participants.count(email) == 1
    assert len(participants) == original_count


def test_signup_rejects_unknown_activity(client):
    # Arrange
    activity_name = "Robotics Club"
    email = "new.student@mergington.edu"

    # Act
    response = client.post(f"/activities/{quote(activity_name, safe='')}/signup", params={"email": email})

    # Assert
    assert response.status_code == 404
    assert response.json() == {"detail": "Activity not found"}


def test_signup_requires_email(client):
    # Arrange
    activity_name = "Chess Club"

    # Act
    response = client.post(f"/activities/{quote(activity_name, safe='')}/signup")

    # Assert
    assert response.status_code == 422
    assert response.json()["detail"][0]["loc"] == ["query", "email"]


def test_unregister_removes_participant_from_activity(client):
    # Arrange
    activity_name = "Chess Club"
    email = "michael@mergington.edu"
    encoded_activity = quote(activity_name, safe="")
    encoded_email = quote(email, safe="")

    # Act
    response = client.delete(f"/activities/{encoded_activity}/participants/{encoded_email}")

    # Assert
    assert response.status_code == 200
    assert response.json() == {"message": f"Unregistered {email} from {activity_name}"}
    assert email not in client.get("/activities").json()[activity_name]["participants"]


def test_unregister_rejects_unknown_activity(client):
    # Arrange
    activity_name = "Robotics Club"
    email = "student@mergington.edu"

    # Act
    response = client.delete(
        f"/activities/{quote(activity_name, safe='')}/participants/{quote(email, safe='')}"
    )

    # Assert
    assert response.status_code == 404
    assert response.json() == {"detail": "Activity not found"}


def test_unregister_rejects_missing_participant(client):
    # Arrange
    activity_name = "Chess Club"
    email = "not.registered@mergington.edu"
    encoded_activity = quote(activity_name, safe="")
    encoded_email = quote(email, safe="")
    original_participants = client.get("/activities").json()[activity_name]["participants"]

    # Act
    response = client.delete(f"/activities/{encoded_activity}/participants/{encoded_email}")

    # Assert
    assert response.status_code == 404
    assert response.json() == {"detail": "Student is not signed up for this activity"}
    assert client.get("/activities").json()[activity_name]["participants"] == original_participants
