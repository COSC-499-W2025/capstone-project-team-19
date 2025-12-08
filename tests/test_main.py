from src import main
from src import constants

def _fake_files_info():
    """
    Return minimal metadata so parse_zip_file stub looks like the real thing.
    Needed because main() now passes the parse results straight into the project
    classification workflow, which expects items shaped like real metadata rows.
    """
    return [
        {
            "file_path": "project_alpha/app.py",
            "file_name": "app.py",
        }
    ]

def test_main_prints_message_verbose(monkeypatch, capsys):
    """
    Happy path: verbose = y, fake zip, classification = individual.
    Just verify the welcome banner still appears.
    """
    # username, menu choice, verbose=y, zip path, overall scope=i
    inputs = iter(['john', '1', 'y', 'fake_path.zip', 'i'])
    monkeypatch.setattr('builtins.input', lambda _='': next(inputs))

    # Patch the names bound in src.main
    monkeypatch.setattr('src.main.get_user_consent', lambda: 'accepted')
    monkeypatch.setattr('src.main.get_external_consent', lambda: 'accepted')

    # Avoid real parsing
    monkeypatch.setattr('src.main.parse_zip_file',
                        lambda *args, **kwargs: _fake_files_info())

    main.main()
    captured = capsys.readouterr()
    assert "Welcome aboard! Let's turn your work into cool insights." in captured.out


def test_main_prints_message_non_verbose(monkeypatch, capsys):
    """
    Same as above, but verbose = n. Behaviour should still show banner.
    """
    # username, menu choice, verbose=n, zip path, overall scope=i
    inputs = iter(['john', '1', 'n', 'fake_path.zip', 'i'])
    monkeypatch.setattr('builtins.input', lambda _='': next(inputs))

    monkeypatch.setattr('src.main.get_user_consent', lambda: 'accepted')
    monkeypatch.setattr('src.main.get_external_consent', lambda: 'accepted')
    monkeypatch.setattr('src.main.parse_zip_file',
                        lambda *args, **kwargs: _fake_files_info())

    main.main()
    captured = capsys.readouterr()
    assert "Welcome aboard! Let's turn your work into cool insights." in captured.out


def test_main_prints_error_non_verbose(monkeypatch, capsys):
    """
    Error path: verbose = n, parse_zip_file fails once,
    then user enters blank path to exit.
    """
    # username, menu choice, verbose=n, first zip (fails), second zip = '' (exit)
    inputs = iter(['jane', '1', 'n', 'non-existent.zip', ''])
    monkeypatch.setattr('builtins.input', lambda _='': next(inputs))

    monkeypatch.setattr('src.main.get_user_consent', lambda: 'accepted')
    monkeypatch.setattr('src.main.get_external_consent', lambda: 'accepted')

    # Force parse failure
    monkeypatch.setattr('src.main.parse_zip_file',
                        lambda *args, **kwargs: False)

    main.main()
    captured = capsys.readouterr()
    # From run_zip_ingestion_flow when parse_zip_file returns falsy
    assert "No valid files were processed" in captured.out


def test_main_prints_error_verbose(monkeypatch, capsys):
    """
    Same error scenario, but verbose = y.
    """
    # username, menu choice, verbose=y, first zip (fails), second zip = '' (exit)
    inputs = iter(['jane', '1', 'y', 'non-existent.zip', ''])
    monkeypatch.setattr('builtins.input', lambda _='': next(inputs))

    monkeypatch.setattr('src.main.get_user_consent', lambda: 'accepted')
    monkeypatch.setattr('src.main.get_external_consent', lambda: 'accepted')

    monkeypatch.setattr('src.main.parse_zip_file',
                        lambda *args, **kwargs: False)

    main.main()
    captured = capsys.readouterr()
    assert "No valid files were processed" in captured.out

def test_verbose_invalid_then_valid(monkeypatch, capsys):
    """
    If user enters an invalid verbose input (not y/n),
    the program should re-prompt until valid.
    """

    # inputs:
    # username = "lily"
    # menu option = 1
    # verbose invalid => "maybe"
    # verbose valid => "n"
    # zip path
    # project scope
    inputs = iter(["lily", "1", "maybe", "n", "fake.zip", "i"])
    monkeypatch.setattr("builtins.input", lambda _='': next(inputs))

    monkeypatch.setattr("src.main.get_user_consent", lambda: "accepted")
    monkeypatch.setattr("src.main.get_external_consent", lambda: "accepted")
    monkeypatch.setattr("src.main.parse_zip_file", lambda *a, **k: _fake_files_info())

    main.main()

    out = capsys.readouterr().out

    # --- must detect invalid verbose ---
    assert "Invalid choice" in out or "Please enter y or n" in out

    # normal welcome should still print afterwards
    assert "Welcome aboard! Let's turn your work into cool insights." in out
