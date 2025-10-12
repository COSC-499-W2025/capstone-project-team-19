from src import main

def test_main_prints_message(monkeypatch, capsys):
    # mock input so main does not wait for user input while testing
    monkeypatch.setattr('builtins.input', lambda _: 'fake_path.zip')

    main.main()
    captured = capsys.readouterr()
    assert "Welcome aboard! Let’s turn your work into cool insights." in captured.out

def test_main_prints_error(monkeypatch, capsys):
    # mock input so main does not wait for user input while testing
    monkeypatch.setattr('builtins.input', lambda _: 'non-existent.zip')

    main.main()
    captured = capsys.readouterr()
    assert "Error" in captured.out
