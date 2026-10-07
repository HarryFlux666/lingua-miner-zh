import json
from unittest.mock import Mock

import pytest
from fastapi.testclient import TestClient

from app import config, languages, main, setup_zh


@pytest.fixture
def english_chinese():
    config.SETTINGS_PATH.write_text(
        json.dumps({"language": "en", "base_language": "zh", "ui_lang": "zh"}),
        encoding="utf-8")


def test_new_install_defaults_to_english_and_chinese():
    config.SETTINGS_PATH.unlink()
    settings = TestClient(main.app).get("/api/settings").json()
    assert settings["language"] == languages.active_code() == "en"
    assert settings["ui_lang"] == "zh"
    assert settings["base_language_effective"] == languages.base_code() == "zh"
    assert settings["default_whisper"] == main.TranscribeReq().model == "small"
    spec = languages.translate_spec()
    assert spec["token"] == ">>cmn_Hans<<"
    assert spec["dir"] == "translate-eng-zho"


def test_chinese_lookup_keeps_definitions_without_loading_translator(monkeypatch, english_chinese):
    monkeypatch.setattr(main.nlp, "analyze_selection", lambda *args: ("bank", "NOUN"))
    monkeypatch.setattr(main.nlp, "zipf", lambda *args: 5.0)
    monkeypatch.setattr(main.ipa, "ipa", lambda *args: "bæŋk")
    monkeypatch.setattr(main.userdict, "lookup", lambda *args: [("n. 银行；河岸", "ECDICT")])
    forbidden = Mock(side_effect=AssertionError("Hover must not load sentence translation"))
    monkeypatch.setattr(main.translate, "sentence", forbidden)
    monkeypatch.setattr(main.translate, "translate", forbidden)
    result = TestClient(main.app).post("/api/lookup", json={
        "selection": "bank", "sentence": "I went to the bank."}).json()
    assert result["ipa"] == "bæŋk"
    assert result["userdefs"][0]["text"] == "n. 银行；河岸"
    assert result["sentence_es"] == result["word_es"] == ""
    forbidden.assert_not_called()


def test_installed_dictionary_does_not_download_again(monkeypatch):
    existing = {"slug": setup_zh.ECDICT_SLUG, "entries": 123}
    monkeypatch.setattr(setup_zh.userdict, "list_dicts", lambda: [existing])
    request = Mock(side_effect=AssertionError("Already installed"))
    monkeypatch.setattr(setup_zh.requests, "get", request)
    assert setup_zh.ensure_dictionary() == existing
    request.assert_not_called()


def test_damaged_archive_never_replaces_user_dictionary(monkeypatch, tmp_path):
    monkeypatch.setattr(setup_zh.userdict, "list_dicts", lambda: [])
    importer = Mock(side_effect=AssertionError("Do not import corrupted data"))
    monkeypatch.setattr(setup_zh.userdict, "import_file", importer)
    bad = tmp_path / "ecdict.zip"
    bad.write_bytes(b"broken download")
    with pytest.raises(ValueError, match="校验失败"):
        setup_zh.ensure_dictionary(bad)
    importer.assert_not_called()
