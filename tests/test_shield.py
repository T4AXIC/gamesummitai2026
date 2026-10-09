from perde import leaked_values, mask, restore
from perde.recognizers import iban_ok, luhn_ok


def entities(text):
    return {s.entity: s.text for s in mask(text).spans}


def test_fin_with_context():
    assert entities("FIN kodum 5ZK3L8M")["FIN"] == "5ZK3L8M"


def test_az_phone_formats():
    for phone in ["+994 50 123 45 67", "+994501234567", "050-123-45-67", "(012) 555 12 34"]:
        assert "PHONE" in entities(f"Əlaqə: {phone}"), phone


def test_bracketed_landline_masked_with_its_bracket():
    assert entities("Tel: (012) 555 12 34")["PHONE"] == "(012) 555 12 34"


def test_house_number_before_full_stop_is_masked():
    assert entities("Ünvan: Sülh küçəsi 12. Tel yoxdur")["ADDRESS"] == "Sülh küçəsi 12"


def test_iban_checksum():
    assert iban_ok("AZ21NABZ00000000137010001944")
    assert not iban_ok("AZ21NABZ00000000137010001945")


def test_voen_needs_context_or_valid_suffix():
    assert entities("VÖEN: 1700123456")["VOEN"] == "1700123456"
    assert "VOEN" not in entities("Sifariş nömrəsi 5550001119")


def test_card_luhn():
    assert luhn_ok("4111111111111111")
    assert "CARD" in entities("Ödəniş 4111 1111 1111 1111 ilə")


def test_person_full_name_with_patronymic():
    assert entities("Mən Əli Vəli oğlu Məmmədov")["PERSON"] == "Əli Vəli oğlu Məmmədov"


def test_greeting_word_is_not_a_name():
    assert "PERSON" not in entities("Hörmətli müştəri, sifarişiniz hazırdır.")


def test_same_value_gets_same_tag():
    r = mask("Aygün zəng etdi. Sonra Aygün yazdı.")
    assert r.masked.count("[PERSON_1]") == 2


def test_same_phone_in_two_formats_gets_one_tag():
    r = mask("Zəng: 050 123 45 67 və ya +994501234567")
    assert r.masked.count("[PHONE_1]") == 2


def test_restore_tolerates_model_formatting():
    r = mask("Telefon +994 55 765 43 21")
    assert restore("Nömrə: [ phone_1 ]", r.mapping) == "Nömrə: +994 55 765 43 21"


def test_restore_handles_tags_without_brackets_or_with_dashes():
    r = mask("Aygün, ş/v AZE12345678")
    out = restore("Salam PERSON_1, [PERSON-1], [person 1], ID_CARD_1.", r.mapping)
    assert out == "Salam Aygün, Aygün, Aygün, AZE12345678."
    assert restore("MYPERSON_1 PERSON_12", r.mapping) == "MYPERSON_1 PERSON_12"


def test_no_leak_after_masking():
    text = "Rəşad Həsənov, FIN 7XK2M9P, tel 070 222 33 44, rashad@bank.az"
    r = mask(text)
    assert leaked_values(r.masked, r.mapping) == []


def test_leak_check_ignores_values_inside_other_words_and_numbers():
    r = mask("Əli zəng etdi, tel +994 55 765 43 21")
    assert leaked_values("Bəli/xeyr cavabı ver", r.mapping) == []
    assert leaked_values("Tarix 2024-55-76, kod 54 321", r.mapping) == []


def test_gateway_masks_personal_data_in_the_task_too(tmp_path, monkeypatch):
    from perde import gateway
    monkeypatch.setattr(gateway, "AUDIT_PATH", tmp_path / "audit.jsonl")
    res = gateway.run("Tel 055 412 33 90", "Reply to Rəşad Həsənov, FIN 7XK2M9P", provider="mock")
    for value in ("Rəşad Həsənov", "7XK2M9P", "055 412 33 90"):
        assert value not in res.outgoing


def test_gateway_blocks_when_no_data_types_selected(tmp_path, monkeypatch):
    import pytest
    from perde import gateway
    monkeypatch.setattr(gateway, "AUDIT_PATH", tmp_path / "audit.jsonl")
    with pytest.raises(gateway.LeakBlocked):
        gateway.run("Nərmin Quliyeva FIN 6TR9K2L", "", provider="mock", entities=[])


def test_leak_check_catches_unmasked_digits():
    r = mask("Telefon +994 55 765 43 21")
    assert leaked_values("call 0557654321", r.mapping)
