"""Unit tests for Peruvian mobile phone E.164 normalization and WhatsApp Web URLs."""
import pytest
from src.domain.value_objects import TelefonoE164


def test_e164_from_9_digits():
    t = TelefonoE164("989322088")
    assert str(t) == "+51989322088"
    assert t.raw_digits == "51989322088"


def test_e164_from_with_country_code():
    t = TelefonoE164("+51989322088")
    assert str(t) == "+51989322088"


def test_e164_from_spaces_and_hyphens():
    t = TelefonoE164(" 989-322-088 ")
    assert str(t) == "+51989322088"


def test_e164_from_leading_zero():
    t = TelefonoE164("0989322088")
    assert str(t) == "+51989322088"


def test_e164_from_unprefixed_51():
    t = TelefonoE164("51989322088")
    assert str(t) == "+51989322088"


def test_e164_invalid_length():
    with pytest.raises(ValueError, match="Formato telefónico inválido"):
        TelefonoE164("98932208")  # 8 digits


def test_e164_invalid_prefix():
    with pytest.raises(ValueError, match="Formato telefónico inválido"):
        TelefonoE164("889322088")  # Doesn't start with 9


def test_e164_whatsapp_url_generation():
    t = TelefonoE164("989322088")
    url = t.generate_whatsapp_url()
    assert url.startswith("https://wa.me/51989322088?text=")
    assert "TCS%20Per" in url

    custom_url = t.generate_whatsapp_url("Hola candidato")
    assert custom_url == "https://wa.me/51989322088?text=Hola%20candidato"
