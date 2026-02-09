def test_git_identities_collaborative_get_and_post(
    client,
    auth_headers,
    uploaded_git_zip,
    insert_classification,
):
    upload = uploaded_git_zip
    project_key = insert_classification(
        user_id=1,
        upload=upload,
        project_name="ProjectA",
        classification="collaborative",
        project_type="code",
    )

    res = client.get(
        f"/projects/upload/{upload['upload_id']}/projects/{project_key}/git/identities",
        headers=auth_headers,
    )
    assert res.status_code == 200
    data = res.json()["data"]
    options = data["options"]
    emails = {opt["email"] for opt in options}
    assert {"alice@example.com", "bob@example.com"}.issubset(emails)

    post = client.post(
        f"/projects/upload/{upload['upload_id']}/projects/{project_key}/git/identities",
        headers=auth_headers,
        json={"selected_indices": [1], "extra_emails": ["extra@example.com"]},
    )
    assert post.status_code == 200
    post_data = post.json()["data"]
    assert 1 in post_data["selected_indices"]


def test_git_identities_individual_get_empty_options(
    client,
    auth_headers,
    uploaded_git_zip,
    insert_classification,
):
    upload = uploaded_git_zip
    project_key = insert_classification(
        user_id=1,
        upload=upload,
        project_name="ProjectA",
        classification="individual",
        project_type="code",
    )

    res = client.get(
        f"/projects/upload/{upload['upload_id']}/projects/{project_key}/git/identities",
        headers=auth_headers,
    )
    assert res.status_code == 200
    data = res.json()["data"]
    assert data["options"] == []
    assert data["selected_indices"] == []


def test_git_identities_post_individual_is_409(
    client,
    auth_headers,
    uploaded_git_zip,
    insert_classification,
):
    upload = uploaded_git_zip
    project_key = insert_classification(
        user_id=1,
        upload=upload,
        project_name="ProjectA",
        classification="individual",
        project_type="code",
    )

    post = client.post(
        f"/projects/upload/{upload['upload_id']}/projects/{project_key}/git/identities",
        headers=auth_headers,
        json={"selected_indices": [1], "extra_emails": []},
    )
    assert post.status_code == 409
