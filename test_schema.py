from .schema import generate_key, generate_id


def test_generate_key():
    assert generate_key() != ""
    assert len(generate_key(5)) == 5


def test_generate_id():
    assert generate_id() != ""
