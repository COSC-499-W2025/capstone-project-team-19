from src import main

def test_main_prints_message(monkeypatch, capsys):
    # Mock BOTH consent and zip inputs
    inputs = iter(['y', 'fake_path.zip'])   # 1️⃣ consent, 2️⃣ zip path
    monkeypatch.setattr('builtins.input', lambda _: next(inputs))

    main.main()
    captured = capsys.readouterr()
    assert "Welcome aboard! Let’s turn your work into cool insights." in captured.out

def test_main_prints_error(monkeypatch, capsys):
    # Mock BOTH consent and zip inputs
    inputs = iter(['y', 'non-existent.zip'])  # 1️⃣ consent, 2️⃣ bad zip path
    monkeypatch.setattr('builtins.input', lambda _: next(inputs))

    main.main()
    captured = capsys.readouterr()
    assert "Error" in captured.out
