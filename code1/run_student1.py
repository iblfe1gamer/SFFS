"""
SFFS — Student 1 interactive demo runner.

Runs from the code1/ directory (or SFFS root with PYTHONPATH). Demonstrates
key generation, encryption, decryption, hashing, and secure key storage.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Ensure this package directory is importable when run as a script
_CODE1 = Path(__file__).resolve().parent
if str(_CODE1) not in sys.path:
    sys.path.insert(0, str(_CODE1))

from f01_generate_key_pairs import generateKeyPairs
from f02_encrypt_file import encryptFile
from f03_decrypt_file import decryptFile
from f04_generate_hash import generateHash
from f05_verify_hash import verifyHash
from f06_secure_key_storage import secureKeyStorage, retrieveKey


def _menu() -> None:
    out = _CODE1 / "test_output"
    out.mkdir(parents=True, exist_ok=True)
    sample = out / "sample.txt"
    if not sample.exists():
        sample.write_bytes(b"SFFS Student 1 demo sample.\n")
    # Holds last AES key after [2] so [3] can decrypt (demo only — real app uses RSA wrap)
    state: dict = {"aes_key": None}

    while True:
        print("\nSFFS - Student 1: Crypto-Security Demo")
        print("=" * 44)
        print("[1] Generate RSA key pair (public.pem + private bytes in memory)")
        print("[2] Encrypt sample file -> .sffs")
        print("[3] Decrypt .sffs -> restored file")
        print("[4] Hash file + verify integrity")
        print("[5] Secure key storage round-trip (password-protected keystore)")
        print("[0] Exit")
        choice = input("Select: ").strip()

        if choice == "0":
            break
        if choice == "1":
            r = generateKeyPairs(out, key_size=2048)
            print("OK:", r["public_key_path"], "key_id=", r["key_id"])
        elif choice == "2":
            from secrets import token_bytes

            aes = token_bytes(32)
            state["aes_key"] = aes
            sffs = out / "sample.sffs"
            r = encryptFile(sample, aes, sffs)
            print("OK:", r.get("output_path"), "hash_pre=", r.get("hash_pre", "")[:16], "...")
            print("(Use [3] next with this session — key kept in memory for demo only.)")
        elif choice == "3":
            sffs = out / "sample.sffs"
            aes = state.get("aes_key")
            if not sffs.exists() or aes is None:
                print("Run [2] first in this session to create sample.sffs and set the AES key.")
                continue
            dest = out / "restored.txt"
            r = decryptFile(sffs, aes, dest)
            print("OK:", r.get("output_path"))
        elif choice == "4":
            h1 = generateHash(sample)
            h2 = generateHash(sample.read_bytes())
            vr = verifyHash(h1, h2)
            print("verifyHash:", vr)
        elif choice == "5":
            r = generateKeyPairs(out, key_size=2048)
            pk = r["private_key_bytes"]
            ks = out / "demo_keystore.json"
            mp = input("Master password for keystore: ")
            secureKeyStorage(pk, mp, ks)
            mp2 = input("Unlock with same password: ")
            got = retrieveKey(ks, mp2)
            print("Retrieved key bytes length:", len(got))
        else:
            print("Invalid choice.")


if __name__ == "__main__":
    _menu()
