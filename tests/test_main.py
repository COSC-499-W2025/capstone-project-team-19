from src import main

def test_main_prints_message(monkeypatch, capsys):
    inputs = iter(['john', 'fake_path.zip'])
    monkeypatch.setattr('builtins.input', lambda _: next(inputs))

    # Patch the names bound in src.main
    monkeypatch.setattr('src.main.get_user_consent', lambda: 'accepted')
    monkeypatch.setattr('src.main.get_external_consent', lambda: 'accepted')

    # Avoid real parsing
    monkeypatch.setattr('src.main.parse_zip_file', lambda _p, _uid=None: True)

    main.main()
    captured = capsys.readouterr()
    assert "Welcome aboard! Let’s turn your work into cool insights." in captured.out


def test_main_prints_error(monkeypatch, capsys):
    inputs = iter(['jane', 'non-existent.zip'])
    monkeypatch.setattr('builtins.input', lambda _: next(inputs))

    monkeypatch.setattr('src.main.get_user_consent', lambda: 'accepted')
    monkeypatch.setattr('src.main.get_external_consent', lambda: 'accepted')

    # Force parse failure
    monkeypatch.setattr('src.main.parse_zip_file', lambda _p, _uid=None: False)

    main.main()
    captured = capsys.readouterr()
    assert "No valid files were processed" in captured.out
