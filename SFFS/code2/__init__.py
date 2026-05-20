"""
SFFS - Student 2: System-Security Module Package
Functions: createIsolatedSandbox, secureMemoryWipe, authenticateUser,
           monitorProcess, writeAuditLog, emergencyLock
"""

from secure_app_launcher import launch_sandbox_file, resolve_launch

__all__ = ["launch_sandbox_file", "resolve_launch"]
