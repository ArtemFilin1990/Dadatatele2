from src.services.inn import validate_inn


def test_non_digits_inn():
    ok, msg = validate_inn("12ab")
    assert not ok
    assert "только цифры" in msg


def test_wrong_length_inn():
    ok, msg = validate_inn("123456")
    assert not ok
    assert "10 или 12" in msg


def test_valid_10_inn():
    ok, _ = validate_inn("3525405517")
    assert ok
