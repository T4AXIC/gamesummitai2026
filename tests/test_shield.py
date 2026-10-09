from perde import leaked_values, mask, restore
from perde.recognizers import iban_ok, luhn_ok


def entities(text):
    return {s.entity: s.text for s in mask(text).spans}


def test_fin_with_context():
    assert entities("FIN kodum 5ZK3L8M")["FIN"] == "5ZK3L8M"


def test_az_phone_formats():
    for phone in ["+994 50 123 45 67", "+994501234567", "050-123-45-67", "(012) 555 12 34"]:
        assert "PHONE" in entities(f"Əlaqə: {phone}"), phone


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


def test_restore_tolerates_model_formatting():
    r = mask("Telefon +994 55 765 43 21")
    assert restore("Nömrə: [ phone_1 ]", r.mapping) == "Nömrə: +994 55 765 43 21"


def test_no_leak_after_masking():
    text = "Rəşad Həsənov, FIN 7XK2M9P, tel 070 222 33 44, rashad@bank.az"
    r = mask(text)
    assert leaked_values(r.masked, r.mapping) == []


def test_leak_check_catches_unmasked_digits():
    r = mask("Telefon +994 55 765 43 21")
    assert leaked_values("call 0557654321", r.mapping)
