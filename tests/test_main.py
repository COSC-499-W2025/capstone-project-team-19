from src import main

def test_main_prints_message(capsys):
    main.main()
    captured = capsys.readouterr()
    assert "This is the main flow of the system!" in captured.out

def test_main_prints_error(capsys):
    main.main()
    captured = capsys.readouterr()
    assert "This is not correct!" != captured.out
