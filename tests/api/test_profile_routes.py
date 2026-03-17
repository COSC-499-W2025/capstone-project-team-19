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


def test_education_and_certifications_defaults_empty(client, auth_headers, seed_conn):
    seed_conn.execute(
        "INSERT OR IGNORE INTO users(user_id, username, email) VALUES (1, 'test-user', NULL)"
    )
    seed_conn.commit()

    edu_res = client.get("/profile/education", headers=auth_headers)
    assert edu_res.status_code == 200
    edu_body = edu_res.json()
    assert edu_body["success"] is True
    assert edu_body["data"]["entries"] == []

    cert_res = client.get("/profile/certifications", headers=auth_headers)
    assert cert_res.status_code == 200
    cert_body = cert_res.json()
    assert cert_body["success"] is True
    assert cert_body["data"]["entries"] == []


def test_put_education_replaces_entries(client, auth_headers, seed_conn):
    seed_conn.execute(
        "INSERT OR IGNORE INTO users(user_id, username, email) VALUES (1, 'test-user', NULL)"
    )
    seed_conn.commit()

    payload = {
        "entries": [
            {
                "title": "BSc in Computer Science",
                "organization": "UBCO",
                "date_text": "2022 - 2026",
                "description": "Major in data science.",
            },
            {
                "title": "Diploma in Math",
                "organization": "Some College",
                "date_text": "2020 - 2022",
                "description": "Focus on applied math.",
            },
        ]
    }

    res = client.put("/profile/education", headers=auth_headers, json=payload)
    assert res.status_code == 200
    body = res.json()
    assert body["success"] is True
    entries = body["data"]["entries"]
    assert len(entries) == 2
    assert entries[0]["entry_type"] == "education"
    assert entries[0]["title"] == "BSc in Computer Science"
    assert entries[1]["title"] == "Diploma in Math"

    # Replace with a single entry and verify old ones are gone.
    replace_payload = {
        "entries": [
            {
                "title": "MSc in Computer Science",
                "organization": "UBCO",
                "date_text": "2026 - 2028",
                "description": "Graduate program.",
            }
        ]
    }
    res2 = client.put("/profile/education", headers=auth_headers, json=replace_payload)
    assert res2.status_code == 200
    entries2 = res2.json()["data"]["entries"]
    assert len(entries2) == 1
    assert entries2[0]["title"] == "MSc in Computer Science"


def test_put_certifications_replaces_entries(client, auth_headers, seed_conn):
    seed_conn.execute(
        "INSERT OR IGNORE INTO users(user_id, username, email) VALUES (1, 'test-user', NULL)"
    )
    seed_conn.commit()

    payload = {
        "entries": [
            {
                "title": "AWS Cloud Practitioner",
                "organization": "Amazon Web Services",
                "date_text": "2025",
                "description": "Foundational cloud certification.",
            }
        ]
    }

    res = client.put("/profile/certifications", headers=auth_headers, json=payload)
    assert res.status_code == 200
    body = res.json()
    assert body["success"] is True
    entries = body["data"]["entries"]
    assert len(entries) == 1
    assert entries[0]["entry_type"] == "certificate"
    assert entries[0]["title"] == "AWS Cloud Practitioner"

