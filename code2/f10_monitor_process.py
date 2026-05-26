"""
f10_monitor_process.py — Student 2: System-Security Module

Debugger attachment means an attacker runs a tool that pauses the SFFS process
and reads its memory. This is a severe threat because it allows:
- Reading decrypted encryption keys from memory
- Stealing passwords and session tokens
- Escaping the sandbox

Memory scanners scan RAM for encryption key patterns. Tools like Volatility,
Recovery Console, or custom malware can create memory dumps.

Platform APIs:
- Windows: IsDebuggerPresent() and CheckRemoteDebuggerPresent() via kernel32.dll
- Linux: Read /proc/self/status and check TracerPid field (non-zero means traced)

This is a defense-in-depth measure, not a guarantee. Attackers will bypass
some protections. But it adds another layer of security.

Check interval of 500ms balances detection speed with CPU usage.
"""

import ctypes
import itertools
import os
import platform
import psutil
import sys
import threading
import time
from pathlib import Path

# Conditional import for Windows debugger detection API
if platform.system() == "Windows":
    kernel32 = ctypes.windll.kernel32
    # WHY: IsDebuggerPresent() returns non-zero if debugger attached
    # CheckRemoteDebuggerPresent() checks if remote debugger is attached
else:
    kernel32 = None


def isDebuggerPresent() -> bool:
    """
    Check if a debugger is attached to the process.

    Args:
        None

    Returns:
        bool: True if debugger is attached

    Security Notes:
        WHY we check every 500ms:
        - Faster detection = sooner threat response
        - But too frequent = high CPU usage
        - 500ms is a reasonable balance

        WHY this is platform-specific:
        - Windows: Uses kernel32.dll API
        - Linux: Uses /proc filesystem
    """
    if platform.system() == "Windows":
        # Windows: Use kernel32 API
        is_debugger_present = kernel32.IsDebuggerPresent()
        return bool(is_debugger_present)

    elif platform.system() == "Linux":
        # Linux: Read /proc/self/status
        try:
            with open('/proc/self/status', 'r') as f:
                for line in f:
                    if line.startswith('TracerPid:'):
                        tracer_pid = int(line.split()[1])
                        return tracer_pid != 0  # Non-zero means traced
        except (OSError, ValueError):
            return False

    return False


def checkSuspiciousProcesses() -> list:
    """
    Check for suspicious debugging/analysis tools running.

    Args:
        None

    Returns:
        list: List of suspicious process names found
    """
    suspicious = []

    # Get running processes — cap at MAX_PROCS to bound latency on busy systems.
    # WHY: On a system with thousands of processes psutil.process_iter() can
    # take seconds.  Legitimate debuggers typically appear early in the list;
    # capping at 1 000 gives a good detection rate with predictable overhead.
    MAX_PROCS = 1000
    proc_iter = psutil.process_iter(["name", "exe"])
    processes = list(itertools.islice(proc_iter, MAX_PROCS))

    # List of known debugging/analysis tools
    if platform.system() == "Windows":
        suspicious_names = [
            "x64dbg.exe", "ollydbg.exe", "windbg.exe",
            "ida64.exe", "processhacker.exe", "wireshark.exe"
        ]
    elif platform.system() == "Linux":
        suspicious_names = [
            "gdb", "strace", "ltrace", "radare2",
            "frida", "valgrind"
        ]

    # Flag processes matching suspicious names
    for proc in processes:
        try:
            name = proc.name()
            if name in suspicious_names:
                suspicious.append(name)
            # Also check full path for Windows
            if platform.system() == "Windows":
                exe_path = proc.exe()
                if exe_path and any(suspicious_name.lower() in exe_path.lower() for suspicious_name in suspicious_names):
                    if exe_path not in suspicious:
                        suspicious.append(exe_path)
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            continue

    return suspicious


class ProcessMonitor(threading.Thread):
    """
    Background daemon thread that monitors for security threats.

    Args:
        check_interval_ms: How often to check (default 500ms)
        on_threat_detected_callback: Callback function called on threat detection
    """

    def __init__(self, check_interval_ms: int = 500, on_threat_detected_callback=None):
        super().__init__(daemon=True)  # Daemon thread so it doesn't prevent exit
        self.check_interval = check_interval_ms / 1000.0  # Convert to seconds
        self.on_threat_detected = on_threat_detected_callback
        self.threat_detected = threading.Event()  # Event to signal threat
        self._stop_event = threading.Event()

    def run(self):
        """
        Main monitoring loop.

        Checks for debugger attachment and suspicious processes every
        check_interval_ms. On threat detection, calls callback and sets flag.
        """
        while not self._stop_event.is_set():
            # Check for debugger attachment
            if isDebuggerPresent():
                self._handleThreat("DEBUGGER_ATTACHED",
                                   "A debugger has been attached to this process")
                break

            # Check for suspicious processes
            suspicious = checkSuspiciousProcesses()
            if suspicious:
                self._handleThreat("SUSPICIOUS_PROCESS",
                                   f"Suspicious process detected: {', '.join(suspicious)}")
                break

            # Sleep for check interval
            if self._stop_event.wait(self.check_interval):
                break

    def _handleThreat(self, threat_type: str, details: str) -> None:
        """
        Handle a detected threat.

        Args:
            threat_type: Type of threat (DEBUGGER_ATTACHED, SUSPICIOUS_PROCESS)
            details: Details about the threat
        """
        self.threat_detected.set()
        self._stop_event.set()

        if self.on_threat_detected:
            try:
                self.on_threat_detected(threat_type, details)
            except Exception:
                pass  # Don't let callback crash the monitor

    def stop(self) -> None:
        """
        Stop the monitoring thread cleanly.

        Sets an event to terminate the loop.
        """
        # Signal to stop monitoring and allow caller to join this daemon cleanly.
        self._stop_event.set()


if __name__ == "__main__":
    print("SFFS — Process Monitor Demo\n" + "=" * 40 + "\n")

    # Start the monitor
    monitor = ProcessMonitor(check_interval_ms=500, on_threat_detected_callback=None)
    monitor.start()

    print("Monitoring... (press Ctrl+C to stop)")
    print(f"Check interval: {500}ms")

    try:
        # Run for 10 seconds for demo purposes
        for i in range(10):
            # Check results
            debugger = isDebuggerPresent()
            suspicious = checkSuspiciousProcesses()

            print(f"\n[{i+1}.0s] Debugger attached: {debugger}")
            print(f"           Suspicious processes: {suspicious if suspicious else 'None'}")

            time.sleep(2)
    except KeyboardInterrupt:
        print("\nStopping monitor...")
        monitor.stop()
        print("Monitor stopped cleanly.")

    print("\n" + "=" * 40)
    print("Demo complete")