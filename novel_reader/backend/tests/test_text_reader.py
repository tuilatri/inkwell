from app.services.text_reader import TextReadError, read_text


def test_utf8_file(tmp_path):
    path = tmp_path / "a.txt"
    path.write_text("Chương 1 — tiếng Việt", encoding="utf-8")
    result = read_text(path)
    assert result.encoding.startswith("utf-8")
    assert "tiếng Việt" in result.text


def test_cp1252_fallback(tmp_path):
    path = tmp_path / "old.txt"
    path.write_bytes(b"Chapter one \x93quoted\x94")
    result = read_text(path)
    assert result.encoding == "cp1252"
    assert "quoted" in result.text


def test_undecodable_file_raises(tmp_path):
    path = tmp_path / "bad.txt"
    path.write_bytes(b"\x81\x8d\x8f")
    try:
        read_text(path)
    except TextReadError:
        pass
    else:
        raise AssertionError("expected TextReadError")
