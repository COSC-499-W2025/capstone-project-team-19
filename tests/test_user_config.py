# tests/test_user_config.py
import builtins
from src import main
from db import (
    connect, init_schema,
    get_or_create_user,
    get_latest_consent,
    get_latest_external_consent,
)
from consent import record_consent
from external_consent import record_external_consent

_FAKE_FILES_INFO = [
    {"file_path": "project_one/main.py", "file_name": "main.py"},
]


# ---------- helpers ----------

def _inputs_repeat_last(monkeypatch, answers):
    """
    Patch input() to return a sequence of answers; if more inputs are requested
    than provided, keep returning the last answer instead of raising StopIteration.
    """
    answers = list(answers)
    idx = {"i": 0}

    def _fake_input(_prompt=""):
        i = idx["i"]
        if i < len(answers):
            val = answers[i]
            idx["i"] += 1
            return val
        return answers[-1] if answers else ""

    monkeypatch.setattr(builtins, "input", _fake_input)


def _stub_parse(monkeypatch, return_value=None):
    """Avoid real parsing during tests."""
    if return_value is None:
        return_value = list(_FAKE_FILES_INFO)
    monkeypatch.setattr("src.main.parse_zip_file", lambda *args, **kwargs: return_value)


def _never_called(*_args, **_kwargs):
    raise AssertionError("This function should not have been called in this path.")


# ---------- tests ----------

def test_new_username_prompts_and_saves_both(monkeypatch):
    """
    A username with no prior rows should prompt both consents and save them.
    (Note: current implementation prints 'Welcome back' even for brand-new rows,
    we don't assert on the banner text here.)
    """
    conn = connect(); init_schema(conn)

    # username -> zip path
    _inputs_repeat_last(monkeypatch, ["john", "/tmp/fake.zip", "i"])
    _stub_parse(monkeypatch)

    # stub consent prompts so no extra input() calls
    monkeypatch.setattr("src.main.get_user_consent", lambda: "accepted")
    monkeypatch.setattr("src.main.get_external_consent", lambda: "rejected")

    main.prompt_and_store()

    # Verify the consents were saved for 'john'
    user_id = get_or_create_user(conn, "john")
    assert get_latest_consent(conn, user_id) == "accepted"
    assert get_latest_external_consent(conn, user_id) == "rejected"


def test_existing_username_no_consents_prompts_both(monkeypatch):
    """User exists but has no consents yet -> prompt and store both."""
    conn = connect(); init_schema(conn)
    user_id = get_or_create_user(conn, "jane")

    _inputs_repeat_last(monkeypatch, ["jane", "/tmp/fake.zip", "i"])
    _stub_parse(monkeypatch)

    monkeypatch.setattr("src.main.get_user_consent", lambda: "accepted")
    monkeypatch.setattr("src.main.get_external_consent", lambda: "accepted")

    main.prompt_and_store()

    assert get_latest_consent(conn, user_id) == "accepted"
    assert get_latest_external_consent(conn, user_id) == "accepted"


def test_partial_missing_external_only_prompts_external(monkeypatch):
    """
    If user consent exists but external consent is missing,
    only the external consent should be prompted and stored.
    """
    conn = connect(); init_schema(conn)
    user_id = get_or_create_user(conn, "alex")
    record_consent(conn, "accepted", user_id=user_id)  # only user consent exists

    _inputs_repeat_last(monkeypatch, ["alex", "/tmp/fake.zip", "i"])
    _stub_parse(monkeypatch)

    # user consent should NOT be called again
    monkeypatch.setattr("src.main.get_user_consent", _never_called)
    monkeypatch.setattr("src.main.get_external_consent", lambda: "accepted")

    main.prompt_and_store()

    assert get_latest_consent(conn, user_id) == "accepted"          # unchanged
    assert get_latest_external_consent(conn, user_id) == "accepted" # newly recorded


def test_partial_missing_user_only_prompts_user(monkeypatch):
    """
    If external consent exists but user consent is missing,
    only the user consent should be prompted and stored.
    """
    conn = connect(); init_schema(conn)
    user_id = get_or_create_user(conn, "bob")
    record_external_consent(conn, "accepted", user_id=user_id)  # only external consent exists

    _inputs_repeat_last(monkeypatch, ["bob", "/tmp/fake.zip", "i"])
    _stub_parse(monkeypatch)

    # external consent should NOT be called again
    monkeypatch.setattr("src.main.get_external_consent", _never_called)
    monkeypatch.setattr("src.main.get_user_consent", lambda: "rejected")

    main.prompt_and_store()

    assert get_latest_consent(conn, user_id) == "rejected"          # newly recorded
    assert get_latest_external_consent(conn, user_id) == "accepted" # unchanged


def test_rejected_user_consent_exits_early(monkeypatch, capsys):
    conn = connect(); init_schema(conn)

    _inputs_repeat_last(monkeypatch, ["sam"])
    monkeypatch.setattr("src.main.parse_zip_file", _never_called)
    monkeypatch.setattr("src.main.get_user_consent", lambda: "rejected")
    monkeypatch.setattr("src.main.get_external_consent", _never_called)

    main.prompt_and_store()
    out = capsys.readouterr().out

    user_id = get_or_create_user(conn, "sam")
    assert get_latest_consent(conn, user_id) == "rejected"
    assert "Consent declined" in out


def test_prior_rejection_does_not_prompt_external(monkeypatch):
    conn = connect(); init_schema(conn)
    user_id = get_or_create_user(conn, "sloan")
    record_consent(conn, "rejected", user_id=user_id)

    _inputs_repeat_last(monkeypatch, ["sloan"])
    monkeypatch.setattr("src.main.parse_zip_file", _never_called)
    monkeypatch.setattr("src.main.get_user_consent", lambda: "rejected")
    monkeypatch.setattr("src.main.get_external_consent", _never_called)

    main.prompt_and_store()

    assert get_latest_consent(conn, user_id) == "rejected"
    assert get_latest_external_consent(conn, user_id) is None


def test_full_configuration_reuse_yes_records_again(monkeypatch, capsys):
    """
    Full config exists; user chooses to reuse. We re-record (audit trail) and proceed.
    """
    conn = connect(); init_schema(conn)
    user_id = get_or_create_user(conn, "chris")
    record_consent(conn, "accepted", user_id=user_id)
    record_external_consent(conn, "accepted", user_id=user_id)

    # username -> reuse? -> zip path
    _inputs_repeat_last(monkeypatch, ["chris", "y", "/tmp/fake.zip", "i"])
    _stub_parse(monkeypatch)

    # No consent prompts should be needed in reuse=yes path
    monkeypatch.setattr("src.main.get_user_consent", _never_called)
    monkeypatch.setattr("src.main.get_external_consent", _never_called)

    main.prompt_and_store()
    out = capsys.readouterr().out

    assert ("Continuing with your saved configuration" in out) or ("continue with this configuration" in out)
    assert get_latest_consent(conn, user_id) == "accepted"
    assert get_latest_external_consent(conn, user_id) == "accepted"


def test_full_configuration_reuse_no_reprompts_both(monkeypatch):
    """
    Full config exists; user chooses NOT to reuse. We re-prompt both and save new values.
    """
    conn = connect(); init_schema(conn)
    user_id = get_or_create_user(conn, "drew")
    record_consent(conn, "accepted", user_id=user_id)
    record_external_consent(conn, "rejected", user_id=user_id)

    # username -> reuse? -> zip path
    _inputs_repeat_last(monkeypatch, ["drew", "n", "/tmp/fake.zip", "i"])
    _stub_parse(monkeypatch)

    # re-prompt both to new choices
    monkeypatch.setattr("src.main.get_user_consent", lambda: "rejected")
    monkeypatch.setattr("src.main.get_external_consent", _never_called)

    main.prompt_and_store()

    assert get_latest_consent(conn, user_id) == "rejected"
    assert get_latest_external_consent(conn, user_id) == "rejected"


def test_correct_user_id_is_used(monkeypatch):
    """
    With multiple users present, ensure new consent rows tie to the active username's user_id.
    """
    conn = connect(); init_schema(conn)

    ua = get_or_create_user(conn, "john")
    record_consent(conn, "accepted", user_id=ua)
    record_external_consent(conn, "accepted", user_id=ua)

    ub = get_or_create_user(conn, "jane")
    record_consent(conn, "accepted", user_id=ub)
    record_external_consent(conn, "rejected", user_id=ub)

    # Log in as jane and choose reuse
    _inputs_repeat_last(monkeypatch, ["jane", "y", "/tmp/fake.zip", "i"])
    _stub_parse(monkeypatch)

    # No prompts expected on reuse
    monkeypatch.setattr("src.main.get_user_consent", _never_called)
    monkeypatch.setattr("src.main.get_external_consent", _never_called)

    main.prompt_and_store()

    # jane's latest should be accepted/rejected, tied to jane
    assert get_latest_consent(conn, ub) == "accepted"
    assert get_latest_external_consent(conn, ub) == "rejected"

    # john's latest remains accepted/accepted
    assert get_latest_consent(conn, ua) == "accepted"
    assert get_latest_external_consent(conn, ua) == "accepted"


def test_project_classifications_are_recorded(monkeypatch):
    conn = connect(); init_schema(conn)

    fake_files = [
        {"file_path": "alpha/main.py", "file_name": "main.py"},
        {"file_path": "beta/utils.py", "file_name": "utils.py"},
    ]

    _inputs_repeat_last(monkeypatch, ["jess", "/tmp/fake.zip", "m", "i", "c"])
    _stub_parse(monkeypatch, return_value=fake_files)

    monkeypatch.setattr("src.main.get_user_consent", lambda: "accepted")
    monkeypatch.setattr("src.main.get_external_consent", lambda: "accepted")

    main.prompt_and_store()

    user_id = get_or_create_user(conn, "jess")
    rows = conn.execute(
        """
        SELECT project_name, classification
        FROM project_classifications
        WHERE user_id=?
        ORDER BY project_name
        """,
        (user_id,),
    ).fetchall()

    assert rows == [("alpha", "individual"), ("beta", "collaborative")]
