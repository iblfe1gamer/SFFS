<!-- converted from SFFS_Functions_Breakdown.docx -->

SFFS
Smart File Fortify System
System Functions Breakdown
Applied Science Private University  |  Faculty of Information Technology
Ibraheem Snineh  |  Karim Taha  |  Mazin Alsarahin
Supervised by: Ismat Aldmour

Function Module Overview

# F-01 · Authentication Module
The Authentication Module is the entry point and gatekeeper of SFFS. It controls all login, logout, password management, and session security operations. Every action within the system requires a valid authenticated session.

## Core Responsibilities
- Validate user credentials before granting system access
- Enforce strong password policies (length, complexity, expiry)
- Manage session lifecycle — start, lock, and terminate
- Support recovery key generation and password reset flow
- Trigger resource isolation immediately upon login


## Authentication Flow
1.  User enters credentials on the login screen.
2.  validateCredentials() checks against the stored password hash.
3.  enforcePasswordPolicy() ensures the password meets security standards.
4.  On success → session is started, IsolatedEnvironment is initialized.
5.  On failure → error is shown, audit log entry is written; account locks after repeated failures.
6.  Idle timeout triggers lockSession(), requiring re-authentication.


# F-02 · Encryption Engine
The Encryption Engine is the cryptographic core of SFFS. It uses AES-256 (Advanced Encryption Standard with a 256-bit key) to protect file content. All encrypt and decrypt operations route through this module, and each operation is automatically linked to integrity hash generation and secure key handling.

## Core Responsibilities
- Encrypt file data using AES-256 (CBC or GCM mode)
- Decrypt previously encrypted files within the isolated environment
- Generate unique encryption keys per file operation
- Coordinate with KeyManager to store and retrieve AES keys
- Coordinate with IntegrityChecker to generate/verify SHA-256 hashes before and after operations


## Encryption Process
Encrypt:  FileManager → raw bytes → EncryptionEngine → generateEncryptionKey() → KeyManager.storeKey() → AES-256 encrypt → IntegrityChecker.generateHash() → write encrypted file.

Decrypt:  Read encrypted file → IntegrityChecker.verifyIntegrity() → KeyManager.retrieveKey() → AES-256 decrypt → expose inside IsolatedEnvironment only.


# F-03 · Key Management Module
The Key Management Module is responsible for the entire lifecycle of cryptographic keys within SFFS. It generates RSA key pairs, stores AES session keys securely, and provides key retrieval and backup capabilities. It is the only module that ever holds raw key material.

## Core Responsibilities
- Generate RSA public/private key pairs for identity and key wrapping
- Securely store AES encryption keys on USB in an encrypted format
- Retrieve keys on demand for the Encryption Engine
- Back up encrypted keys to the cloud via the Cloud Backup Module
- Wipe keys from memory immediately after use


## Key Storage Architecture
AES keys are never stored in plain text. Each AES key is wrapped (encrypted) using the user's RSA public key before being written to a secure key store on the USB. Retrieval requires the RSA private key, which itself is protected by the user's master password.


# F-04 · Integrity Verification Module
The Integrity Verification Module uses SHA-256 hashing to guarantee that files have not been tampered with, corrupted, or altered — either during storage, transfer, or decryption. It is called automatically by the Encryption Engine on both encrypt and decrypt operations.

## Core Responsibilities
- Compute SHA-256 checksums for files before encryption
- Store checksum alongside encrypted file metadata
- Re-compute and compare checksum after decryption to detect tampering
- Raise a security alert if integrity verification fails



# F-05 · Isolated Execution Environment
The Isolated Execution Environment is the most architecturally significant module in SFFS. It creates a sandboxed runtime that prevents the host operating system, running processes, or malware from accessing decrypted file content. This is the key differentiator that addresses the primary limitation of existing encryption tools.

## Core Responsibilities
- Isolate all file decryption and active usage from the host OS
- Prevent host processes and malware from reading decrypted file bytes
- Manage temporary encrypted storage inside the USB for active files
- Start and stop the secure environment on demand
- Wipe all temporary decrypted data when the session ends


## How Isolation Works
On login, isolateResources() intercepts file system calls from the application and redirects them to an encrypted virtual storage area on the USB drive. The host OS sees only encrypted bytes. Decrypted content exists only within the application's protected memory space.
When the user logs out, removes the USB, or the session times out, wipeTemporaryData() uses secure-delete techniques to overwrite and remove all temporary decrypted content — preventing forensic recovery.


# F-06 · File Manager
The File Manager handles all file system interactions on behalf of the application. It is the only module permitted to perform raw file I/O, and all its operations are routed through the Isolated Execution Environment. It provides the Encryption Engine with file bytes and writes encrypted output back to storage.

## Core Responsibilities
- Let users select files via the UI (including drag-and-drop)
- Read raw file bytes for encryption
- Write encrypted or decrypted files to the appropriate location
- Delete files with secure-wipe capability
- Enforce that all I/O passes through the IsolatedEnvironment


# F-07 · Cloud Backup Module
The Cloud Backup Module provides optional, encrypted backup and restore functionality via the Google Drive API. It allows users to safely back up their encrypted keys and files to the cloud, ensuring recovery is possible even if the USB is lost or damaged — without ever exposing plaintext data to the cloud provider.

## Core Responsibilities
- Authenticate with Google Drive using OAuth 2.0
- Upload encrypted file backups and encrypted key archives
- Download and restore backups on demand
- Ensure all data is encrypted before leaving the USB device
- Operate entirely within the IsolatedEnvironment



# F-08 · Audit Logger
The Audit Logger provides a tamper-resistant, encrypted audit trail of all significant events within SFFS. It records authentication attempts, file operations, key accesses, backup events, and security alerts. Log files are encrypted and stored on the USB drive, and rotate automatically to prevent overflow.

## Core Responsibilities
- Record all security-relevant events with timestamp and severity
- Encrypt log files to prevent tampering or unauthorized reading
- Rotate logs automatically when maximum size is reached (FIFO)
- Provide a read-only log viewer via the UIController
- Write logs synchronously to ensure no events are lost


## Events Logged
The following event categories are captured by the Audit Logger:
- Authentication: login success, login failure, lockout, logout, password change
- File Operations: encrypt, decrypt, delete, select — with file size and timestamp
- Key Operations: generate, store, retrieve, backup — key ID only, never raw key
- Integrity: hash generated, verification passed, verification failed (CRITICAL)
- Environment: isolation started, stopped, wiped, timeout
- Cloud: backup uploaded, backup restored, cloud auth failure

# F-09 · UI Controller
The UI Controller is the presentation layer of SFFS. It provides the user-facing dashboard, drag-and-drop file interface, real-time progress tracking, security alerts, and log viewer. It translates user actions into commands for the underlying modules and surfaces system feedback in an accessible way.

## Core Responsibilities
- Render the login screen and main dashboard (PyQt / PySide)
- Handle drag-and-drop file selection and pass paths to FileManager
- Display real-time progress bars for encryption/decryption operations
- Show security alerts (integrity failure, malware detection, auth lockout)
- Provide a cloud sync panel and settings configuration screen
- Display the encrypted audit log via a read-only log viewer



# F-10 · Configuration & Database Manager
The Configuration & Database Manager handles persistent storage of application settings, user preferences, and non-sensitive operational data using SQLite. It also manages JSON/YAML configuration files for portability. All stored data is encrypted or hashed — no plaintext sensitive information is ever written to disk.

## Core Responsibilities
- Store and retrieve user settings (timeout, cloud toggle, UI preferences)
- Maintain an SQLite database for operational metadata
- Manage encrypted JSON configuration files on the USB
- Provide configuration to all modules on startup


# Module Interaction Summary
The diagram below outlines how the ten functional modules interconnect. The Authentication Module and Isolated Environment form the security perimeter — every other module operates within these boundaries.


## Key Integration Points
- Authentication Module activates Isolated Environment on successful login
- Every encrypt/decrypt call chains: FileManager → EncryptionEngine → KeyManager + IntegrityChecker
- Every module writes to AuditLogger — it is the universal observer
- UI Controller is the single point of human interaction; it delegates everything to backend modules
- Cloud Backup operates only after Authentication and only inside the IsolatedEnvironment
- Configuration Manager is initialized first on startup and queried by all modules

SFFS — Smart File Fortify System  |  Applied Science Private University  |  2025
| ID | Module | Category | Responsibility |
| --- | --- | --- | --- |
| F-01 | Authentication Module | Security Layer | Login, password management, MFA enforcement |
| F-02 | Encryption Engine | Crypto Core | AES-256 file encryption and decryption |
| F-03 | Key Management Module | Crypto Core | RSA key generation, storage, and retrieval |
| F-04 | Integrity Verification | Data Validation | SHA-256 checksum generation and verification |
| F-05 | Isolated Execution Env. | Security Layer | Sandboxed runtime for secure file operations |
| F-06 | File Manager | Core Logic | File selection, read, write, and deletion |
| F-07 | Cloud Backup Module | Storage/Recovery | Encrypted backup and restore via Google Drive |
| F-08 | Audit Logger | Monitoring | Secure event logging and log management |
| F-09 | UI Controller | Presentation | Dashboard, drag-drop, progress, alerts |
| F-10 | Configuration & DB Manager | Storage | SQLite/JSON config storage and retrieval |
| F-01  Authentication Module   [Security Layer] | F-01  Authentication Module   [Security Layer] |
| --- | --- |
| Description | Handles identity verification, session control, and credential management. Acts as the primary access gate — no other module is activated without a valid authenticated session. |
| Inputs | • Username / password input
• Recovery key (for reset)
• Session timeout configuration |
| Outputs | • Authenticated session token
• Error/reject messages
• Audit log entries for auth events |
| Methods | • validateCredentials(u, p): boolean
• enforcePasswordPolicy(p): boolean
• lockSession(userId): void
• resetPassword(userId): String
• logout(): void |
| Dependencies | • IsolatedEnvironment (triggers on login)
• AuditLogger (logs auth events)
• UIController (displays login screen / errors)
• KeyManager (manages recovery key) |
| Security Notes
• Passwords are never stored in plain text — SHA-256 hashed with salt
• Maximum login attempts enforced before temporary lockout
• Session token is invalidated on logout, USB removal, or timeout
• All authentication events (success, fail, lock) are written to AuditLogger |
| --- |
| F-02  Encryption Engine   [Crypto Core] | F-02  Encryption Engine   [Crypto Core] |
| --- | --- |
| Description | Performs all AES-256 encryption and decryption operations on files. Every encrypt call triggers key generation (via KeyManager) and hash generation (via IntegrityChecker). Every decrypt call first verifies integrity before exposing data. |
| Inputs | • Raw file byte data
• AES encryption key (from KeyManager)
• Operation mode (encrypt / decrypt) |
| Outputs | • Encrypted file bytes (on encrypt)
• Decrypted file bytes (on decrypt)
• Operation status / error codes |
| Methods | • encryptFile(data: byte[], key: byte[]): byte[]
• decryptFile(data: byte[], key: byte[]): byte[]
• generateEncryptionKey(): byte[] |
| Dependencies | • KeyManager (key storage and retrieval)
• IntegrityChecker (hash before/after operations)
• IsolatedEnvironment (all ops run inside sandbox)
• FileManager (provides raw file bytes)
• AuditLogger (logs encryption events) |
| Technical Details
• Algorithm: AES-256-GCM (provides both encryption and authentication)
• Key size: 256 bits — brute-force resistant
• IV (Initialization Vector): randomly generated per operation
• Keys are never stored alongside encrypted files — managed separately by KeyManager
• Decrypted content is only accessible inside the IsolatedEnvironment sandbox |
| --- |
| F-03  Key Management Module   [Crypto Core] | F-03  Key Management Module   [Crypto Core] |
| --- | --- |
| Description | Manages the full lifecycle of all cryptographic key material. RSA keys provide identity and wrap AES keys for secure storage. AES keys are generated per-file and stored encrypted. Keys are wiped from memory immediately after use. |
| Inputs | • Request for key generation
• Key identifier (keyId)
• Backup flag (cloud or local) |
| Outputs | • RSA public/private key pair
• Stored AES key reference
• Retrieved AES key bytes
• Key backup confirmation |
| Methods | • generateRSAKeys(): void
• storeKeySecurely(key: byte[]): boolean
• retrieveKey(keyId: String): byte[]
• backupKeys(): void |
| Dependencies | • EncryptionEngine (provides AES keys on request)
• CloudBackupModule (for key backup/restore)
• AuditLogger (logs key operations)
• IsolatedEnvironment (key operations run in sandbox) |
| Security Notes
• RSA key size: 2048-bit minimum (4096-bit recommended)
• AES keys are wrapped using RSA-OAEP before storage
• Keys are held in memory only for the duration of the crypto operation
• Memory is zeroed immediately after the key is no longer needed
• Backup copies are encrypted before leaving the device |
| --- |
| F-04  Integrity Verification Module   [Data Validation] | F-04  Integrity Verification Module   [Data Validation] |
| --- | --- |
| Description | Generates and verifies SHA-256 hashes for all file operations. A mismatch between stored hash and re-computed hash indicates file corruption or tampering, and triggers an immediate security alert via UIController. |
| Inputs | • File byte data
• Expected hash value (for verification)
• Hash algorithm setting |
| Outputs | • SHA-256 hash string
• Verification result: pass / fail
• Tamper alert event (on failure) |
| Methods | • generateHash(data: byte[]): String
• verifyIntegrity(data: byte[], expectedHash: String): boolean |
| Dependencies | • EncryptionEngine (called before and after all crypto ops)
• UIController (receives tamper alerts)
• AuditLogger (logs verification results)
• FileManager (provides file bytes) |
| Why SHA-256?
• SHA-256 produces a unique 256-bit fingerprint for any input — even a single changed byte produces a completely different hash
• Computationally infeasible to reverse or forge
• Part of the SHA-2 family, widely trusted in security-critical applications
• Combined with AES-256 encryption, provides both confidentiality AND integrity
• Alternative: BLAKE2 (higher performance for large files) |
| --- |
| F-05  Isolated Execution Environment   [Security Layer] | F-05  Isolated Execution Environment   [Security Layer] |
| --- | --- |
| Description | Creates and manages a sandboxed execution context for all sensitive file operations. Decrypted content is never written to the host system's disk or memory in a readable form. The environment starts on login, and all temporary data is securely wiped on logout or USB removal. |
| Inputs | • Start/stop environment command
• Isolation policy configuration
• Session timeout setting |
| Outputs | • Isolation status (active / inactive)
• Environment ID
• Wipe confirmation on teardown |
| Methods | • startEnvironment(): boolean
• stopEnvironment(): void
• isolateResources(): void
• wipeTemporaryData(): void |
| Dependencies | • AuthenticationModule (triggers start on login)
• EncryptionEngine (all decrypt ops run inside)
• FileManager (all file reads/writes routed through)
• AuditLogger (logs environment events)
• CloudBackupModule (operates inside isolation) |
| Why This Matters
• Existing tools (VeraCrypt, AxCrypt, BitLocker) write decrypted files to host system disk — malware can intercept them
• SFFS decrypted data is only accessible inside the isolated environment
• Even on an infected machine, malware cannot read SFFS-decrypted content from the host OS
• 84 days allocated in the project Gantt chart — largest single task — reflecting its complexity |
| --- |
| F-06  File Manager   [Core Logic] | F-06  File Manager   [Core Logic] |
| --- | --- |
| Description | Provides a controlled interface for all file operations. No other module reads or writes files directly. Supports drag-and-drop file selection, secure deletion, and routes all I/O through the IsolatedEnvironment to prevent host-system exposure. |
| Inputs | • File path (from UI selection or drag-drop)
• File data bytes (for write operations)
• Delete confirmation flag |
| Outputs | • Raw file bytes (for EncryptionEngine)
• Write success/failure status
• File metadata (name, size, type) |
| Methods | • selectFile(path: String): File
• readFile(): byte[]
• writeFile(data: byte[]): boolean
• deleteFile(): boolean |
| Dependencies | • IsolatedEnvironment (all I/O routed through)
• EncryptionEngine (consumer of readFile)
• UIController (provides file path from drag-drop)
• AuditLogger (logs all file operations) |
| F-07  Cloud Backup Module   [Storage / Recovery] | F-07  Cloud Backup Module   [Storage / Recovery] |
| --- | --- |
| Description | Manages optional encrypted cloud backup and restore via Google Drive API. Files and keys are encrypted before upload — the cloud provider never sees plaintext. Restore operations download and decrypt within the IsolatedEnvironment. |
| Inputs | • Google Drive OAuth credentials
• Encrypted file to upload
• Backup restore request |
| Outputs | • Upload confirmation / file ID
• Downloaded encrypted file
• Restore success / failure status |
| Methods | • authenticateCloud(): boolean
• uploadEncryptedFile(file: File): boolean
• downloadEncryptedFile(fileId: String): File
• restoreBackup(): boolean |
| Dependencies | • KeyManager (provides encrypted key archives for backup)
• EncryptionEngine (files are encrypted before upload)
• IsolatedEnvironment (cloud ops run inside sandbox)
• AuditLogger (logs all backup/restore events) |
| Cloud Security Guarantee
• Files are encrypted with AES-256 BEFORE being sent to Google Drive
• Google Drive stores only ciphertext — even a breach of the cloud provider exposes no plaintext
• Keys are backed up separately in their own encrypted archive
• Cloud backup is entirely optional — system is fully functional offline |
| --- |
| F-08  Audit Logger   [Monitoring] | F-08  Audit Logger   [Monitoring] |
| --- | --- |
| Description | Maintains an encrypted, append-only audit trail of all system events. Every module writes to the AuditLogger. Logs are encrypted on disk, rotated on overflow, and viewable only by the authenticated user via the dashboard. |
| Inputs | • Event string
• Severity level (INFO, WARN, ERROR, CRITICAL)
• Calling module identifier |
| Outputs | • Log entry written confirmation
• Log list (for viewer)
• Rotation notification |
| Methods | • logEvent(event: String, level: int): void
• encryptLogs(): void
• rotateLogs(): void
• viewLogs(): List<String> |
| Dependencies | • All modules (universal consumer — every module logs events)
• UIController (log viewer display)
• IsolatedEnvironment (log files stored inside sandbox) |
| F-09  UI Controller   [Presentation] | F-09  UI Controller   [Presentation] |
| --- | --- |
| Description | The user-facing layer that connects all backend modules to the user. Renders screens, handles user interaction (including drag-and-drop), and surfaces real-time feedback. Built with PyQt/PySide for a modern, cross-platform GUI. |
| Inputs | • User interactions (clicks, drag-drop, form input)
• Progress events from EncryptionEngine
• Alert events from IntegrityChecker, AuthModule
• Log data from AuditLogger |
| Outputs | • Screen renders (login, dashboard, settings)
• Progress indicator updates
• Security alert dialogs
• File path selections to FileManager |
| Methods | • loadLoginScreen(): void
• loadDashboard(): void
• showProgress(percent: int): void
• showErrorMessage(msg: String): void
• displaySecurityAlert(severity: int): void |
| Dependencies | • AuthenticationModule (login flow)
• FileManager (drag-drop file paths)
• EncryptionEngine (progress events)
• IntegrityChecker (tamper alerts)
• AuditLogger (log display)
• CloudBackupModule (sync panel) |
| UI Design Principles
• Drag-and-drop as the primary interaction for non-technical users
• Color-coded severity alerts (INFO=blue, WARN=yellow, CRITICAL=red)
• Progress bars and status messages for all long-running operations
• No technical jargon in user-facing messages — plain language throughout
• Settings panel allows cloud backup toggle, timeout configuration, password change |
| --- |
| F-10  Configuration & Database Manager   [Storage] | F-10  Configuration & Database Manager   [Storage] |
| --- | --- |
| Description | Manages all persistent non-cryptographic application data. Provides an SQLite database for operational metadata and encrypted JSON/YAML config files. Called by all modules at startup and when settings change. |
| Inputs | • Setting key-value pairs
• Database queries
• Configuration read requests |
| Outputs | • Setting values
• Query results
• Full configuration object on startup |
| Methods | • getSetting(key): value
• setSetting(key, value): void
• loadConfig(): Config
• saveConfig(config): void |
| Dependencies | • All modules (read config on init)
• AuthenticationModule (timeout, lockout policy)
• UIController (UI preferences)
• CloudBackupModule (cloud toggle, credentials path)
• AuditLogger (log rotation size setting) |
| Security Layer | Crypto Core / Execution | Presentation / Monitoring |
| --- | --- | --- |
| F-01 Authentication | F-05 Isolated Env. | F-09 UI Controller |
| F-02 Encryption Engine | F-03 Key Manager | F-04 Integrity Checker |
| F-06 File Manager | F-07 Cloud Backup | F-08 Audit Logger |
| F-10 Config Manager | — | — |