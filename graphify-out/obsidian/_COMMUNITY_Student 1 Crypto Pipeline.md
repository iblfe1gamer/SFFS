---
type: community
cohesion: 0.07
members: 33
---

# Student 1 Crypto Pipeline

**Cohesion:** 0.07 - loosely connected
**Members:** 33 nodes

## Members
- [[Convenience function to hash a file and return metadata.      Args         path]] - rationale - SFFS\code1\f04_generate_hash.py
- [[Encrypt a file using AES-256-GCM and write to SFFS binary format.      The funct]] - rationale - SFFS\code1\f02_encrypt_file.py
- [[Generate a cryptographic hash of the given data.      Args         target Eith]] - rationale - SFFS\code1\f04_generate_hash.py
- [[Generate an RSA-2048 key pair for SFFS encryptiondecryption.      RSA asymmetri]] - rationale - SFFS\code1\f01_generate_key_pairs.py
- [[SFFS — Student 1 interactive demo runner.  Runs from the code1 directory (or SF]] - rationale - SFFS\code1\run_student1.py
- [[SFFS — Student 1 File Encryption Module  This module encrypts files using AES-2]] - rationale - SFFS\code1\f02_encrypt_file.py
- [[SFFS — Student 1 Hash Generation Module  This module provides cryptographic has]] - rationale - SFFS\code1\f04_generate_hash.py
- [[SFFS — Student 1 Hash Verification Module  This module verifies file integrity]] - rationale - SFFS\code1\f05_verify_hash.py
- [[SFFS — Student 1 RSA Key Pair Generation Module  This module generates RSA-2048]] - rationale - SFFS\code1\f01_generate_key_pairs.py
- [[Student 1 — crypto module tests.]] - rationale - SFFS\tests\test_student1.py
- [[Verify integrity of a file by comparing hashes of original and decrypted version]] - rationale - SFFS\code1\f05_verify_hash.py
- [[Verify that two hashes match using constant-time comparison.      Args]] - rationale - SFFS\code1\f05_verify_hash.py
- [[_menu()]] - code - SFFS\code1\run_student1.py
- [[encryptFile()]] - code - SFFS\code1\f02_encrypt_file.py
- [[f01_generate_key_pairs.py]] - code - SFFS\code1\f01_generate_key_pairs.py
- [[f02_encrypt_file.py]] - code - SFFS\code1\f02_encrypt_file.py
- [[f04_generate_hash.py]] - code - SFFS\code1\f04_generate_hash.py
- [[f05_verify_hash.py]] - code - SFFS\code1\f05_verify_hash.py
- [[generateFileHash()]] - code - SFFS\code1\f04_generate_hash.py
- [[generateHash()]] - code - SFFS\code1\f04_generate_hash.py
- [[generateKeyPairs()]] - code - SFFS\code1\f01_generate_key_pairs.py
- [[run_student1.py]] - code - SFFS\code1\run_student1.py
- [[test_decrypt_restores_original()]] - code - SFFS\tests\test_student1.py
- [[test_encrypt_produces_sffs_file()]] - code - SFFS\tests\test_student1.py
- [[test_hash_detects_tampering()]] - code - SFFS\tests\test_student1.py
- [[test_hash_is_deterministic()]] - code - SFFS\tests\test_student1.py
- [[test_key_pair_generation()]] - code - SFFS\tests\test_student1.py
- [[test_key_retrieval_fails_wrong_password()]] - code - SFFS\tests\test_student1.py
- [[test_student1.py]] - code - SFFS\tests\test_student1.py
- [[test_verify_hash_fails_on_tampered_file()]] - code - SFFS\tests\test_student1.py
- [[test_verify_hash_passes_on_intact_file()]] - code - SFFS\tests\test_student1.py
- [[verifyFileIntegrity()]] - code - SFFS\code1\f05_verify_hash.py
- [[verifyHash()]] - code - SFFS\code1\f05_verify_hash.py

## Live Query (requires Dataview plugin)

```dataview
TABLE source_file, type FROM #community/Student_1_Crypto_Pipeline
SORT file.name ASC
```

## Connections to other communities
- 7 edges to [[_COMMUNITY_SFFSCore Orchestrator and Monitoring]]
- 2 edges to [[_COMMUNITY_RSA Keystore and Wrapping]]

## Top bridge nodes
- [[test_student1.py]] - degree 15, connects to 2 communities
- [[run_student1.py]] - degree 8, connects to 2 communities
- [[f04_generate_hash.py]] - degree 6, connects to 1 community
- [[f05_verify_hash.py]] - degree 6, connects to 1 community
- [[f01_generate_key_pairs.py]] - degree 5, connects to 1 community