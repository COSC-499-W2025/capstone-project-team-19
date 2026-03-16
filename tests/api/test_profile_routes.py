def test_get_profile_defaults_for_new_user(client, auth_headers, seed_conn):
    # Ensure the authenticated user exists in the DB.
    seed_conn.execute(
        "INSERT OR IGNORE INTO users(user_id, username, email) VALUES (1, 'test-user', NULL)"
    )
    seed_conn.commit()

    res = client.get("/profile", headers=auth_headers)
    assert res.status_code == 200
    body = res.json()
    assert body["success"] is True
    profile = body["data"]
    assert profile["user_id"] == 1
    assert profile["email"] is None
    assert profile["full_name"] is None
    assert profile["phone"] is None
    assert profile["linkedin"] is None
    assert profile["github"] is None
    assert profile["location"] is None
    assert profile["profile_text"] is None


def test_put_profile_updates_fields_and_get_returns_them(client, auth_headers, seed_conn):
    seed_conn.execute(
        "INSERT OR IGNORE INTO users(user_id, username, email) VALUES (1, 'test-user', NULL)"
    )
    seed_conn.commit()
    payload = {
        "email": "user@example.com",
        "full_name": "Alice Example",
        "phone": "123-456-7890",
        "linkedin": "https://linkedin.com/in/alice",
        "github": "https://github.com/alice",
        "location": "Wonderland",
        "profile_text": "Experienced engineer.",
    }
    res = client.put("/profile", headers=auth_headers, json=payload)
    assert res.status_code == 200
    body = res.json()
    assert body["success"] is True
    profile = body["data"]
    for key, value in payload.items():
        assert profile[key] == value

    # Subsequent GET returns the same data
    res_get = client.get("/profile", headers=auth_headers)
    assert res_get.status_code == 200
    profile_get = res_get.json()["data"]
    for key, value in payload.items():
        assert profile_get[key] == value


def test_put_profile_clears_fields_with_blank_strings(client, auth_headers, seed_conn):
    seed_conn.execute(
        "INSERT OR IGNORE INTO users(user_id, username, email) VALUES (1, 'test-user', NULL)"
    )
    seed_conn.commit()
    initial = {
        "email": "user@example.com",
        "full_name": "Alice Example",
        "phone": "123-456-7890",
        "linkedin": "https://linkedin.com/in/alice",
        "github": "https://github.com/alice",
        "location": "Wonderland",
        "profile_text": "Experienced engineer.",
    }
    res = client.put("/profile", headers=auth_headers, json=initial)
    assert res.status_code == 200

    # Now clear some fields using blank strings, and leave others unchanged by omitting them.
    update_payload = {
        "email": "",
        "full_name": "",
        "phone": "",
        "linkedin": "",
        "github": "",
        "location": "",
        "profile_text": "",
    }
    res_update = client.put("/profile", headers=auth_headers, json=update_payload)
    assert res_update.status_code == 200
    profile = res_update.json()["data"]

    # All provided blank-string fields should come back as None.
    for key in update_payload.keys():
        assert profile[key] is None


def test_put_profile_rejects_overlong_profile_text(client, auth_headers, seed_conn):
    seed_conn.execute(
        "INSERT OR IGNORE INTO users(user_id, username, email) VALUES (1, 'test-user', NULL)"
    )
    seed_conn.commit()
    long_text = "x" * 601
    res = client.put("/profile", headers=auth_headers, json={"profile_text": long_text})
    assert res.status_code == 400
    body = res.json()
    assert "profile_text must be at most" in body["detail"]

