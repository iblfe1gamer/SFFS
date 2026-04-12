"""Student 1 — crypto module tests."""

from pathlib import Path
from secrets import token_bytes

import pytest

from f01_generate_key_pairs import generateKeyPairs
from f02_encrypt_file import encryptFile
from f03_decrypt_file import SecurityError, decryptFile
from f04_generate_hash import generateHash
from f05_verify_hash import verifyHash
from f06_secure_key_storage import retrieveKey, secureKeyStorage


def test_key_pair_generation(tmp_path: Path) -> None:
    r = generateKeyPairs(tmp_path, key_size=2048)
    assert r["public_key_path"].exists()
    assert r["private_key_bytes"] is not None
    assert len(r["key_id"]) >= 8


def test_encrypt_produces_sffs_file(tmp_path: Path) -> None:
    f = tmp_path / "a.txt"
    f.write_bytes(b"data")
    key = token_bytes(32)
    out = tmp_path / "a.sffs"
    r = encryptFile(f, key, out)
    assert r["sffs_path"] == out
    assert out.exists()
    assert out.read_bytes()[:4] == b"SFFS"


def test_decrypt_restores_original(tmp_path: Path) -> None:
    plain = tmp_path / "p.bin"
    plain.write_bytes(b"Hello World")
    key = token_bytes(32)
    sffs = tmp_path / "p.sffs"
    encryptFile(plain, key, sffs)
    dec = decryptFile(sffs, key, tmp_path)
    restored = Path(dec["output_path"])
    assert restored.read_bytes() == b"Hello World"


def test_hash_is_deterministic(tmp_path: Path) -> None:
    f = tmp_path / "h.txt"
    f.write_bytes(b"same")
    assert generateHash(f) == generateHash(f.read_bytes())


def test_hash_detects_tampering() -> None:
    h1 = generateHash(b"original")
    h2 = generateHash(b"0riginal")
    assert h1 != h2


def test_verify_hash_passes_on_intact_file(tmp_path: Path) -> None:
    plain = tmp_path / "x.bin"
    plain.write_bytes(b"ok")
    key = token_bytes(32)
    sffs = tmp_path / "x.sffs"
    enc = encryptFile(plain, key, sffs)
    dec = decryptFile(sffs, key, tmp_path)
    vr = verifyHash(enc["hash_pre"], dec["hash_post"])
    assert vr["match"] is True
    assert vr["alert_level"] == "OK"


def test_verify_hash_fails_on_tampered_file(tmp_path: Path) -> None:
    plain = tmp_path / "t.bin"
    plain.write_bytes(b"x" * 200)
    key = token_bytes(32)
    sffs = tmp_path / "t.sffs"
    encryptFile(plain, key, sffs)
    raw = bytearray(sffs.read_bytes())
    if len(raw) > 100:
        raw[100] ^= 0xFF
    sffs.write_bytes(raw)
    with pytest.raises(SecurityError):
        decryptFile(sffs, key, tmp_path)


def test_key_retrieval_fails_wrong_password(tmp_path: Path) -> None:
    r = generateKeyPairs(tmp_path, key_size=2048)
    store = secureKeyStorage(r["private_key_bytes"], "correct_pass", tmp_path)
    ks = store["keystore_path"]
    with pytest.raises(ValueError):
        retrieveKey(ks, "wrong_pass")
