from src import main

def test_main_prints_message(monkeypatch, capsys):
    # Mock both consent, external consent and zip inputs
    inputs = iter(['y','y', 'fake_path.zip'])   # consent, zip path
    monkeypatch.setattr('builtins.input', lambda _: next(inputs))

    main.main()
    captured = capsys.readouterr()
    assert "Welcome aboard! Let’s turn your work into cool insights." in captured.out


def test_main_prints_error(monkeypatch, capsys):
    # Mock both consent, external consent and zip inputs
    inputs = iter(['y','y', 'non-existent.zip'])  # consent, bad zip path
    monkeypatch.setattr('builtins.input', lambda _: next(inputs))

    main.main()
    captured = capsys.readouterr()
    assert "Error" in captured.out
