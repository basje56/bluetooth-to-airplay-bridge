"""Audio diagnostics and troubleshooting tools for Bluetooth to AirPlay Bridge."""
from __future__ import annotations

import asyncio
import json
import logging
import subprocess
import time
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

_LOGGER = logging.getLogger(__name__)


@dataclass
class AudioDiagnosticResult:
    """Result of an audio diagnostic test."""
    test_name: str
    status: str  # "pass", "fail", "warning", "info"
    message: str
    details: Dict[str, Any]
    timestamp: str
    duration_ms: int


@dataclass
class SystemAudioInfo:
    """System audio information."""
    bluetooth_available: bool
    gstreamer_available: bool
    pulseaudio_available: bool
    alsa_available: bool
    bluetooth_devices: List[Dict[str, Any]]
    audio_devices: List[Dict[str, Any]]
    system_info: Dict[str, Any]


class AudioDiagnostics:
    """Comprehensive audio diagnostics and troubleshooting."""
    
    def __init__(self) -> None:
        """Initialize audio diagnostics."""
        self._results: List[AudioDiagnosticResult] = []
        
    async def run_full_diagnostics(self) -> Dict[str, Any]:
        """Run complete audio diagnostics suite."""
        _LOGGER.info("Starting comprehensive audio diagnostics")
        start_time = time.time()
        
        self._results.clear()
        
        # System checks
        await self._check_system_requirements()
        await self._check_bluetooth_stack()
        await self._check_audio_stack()
        
        # Device checks
        await self._check_bluetooth_devices()
        await self._check_audio_devices()
        
        # Configuration checks
        await self._check_audio_configuration()
        await self._check_permissions()
        
        # Performance checks
        await self._check_audio_latency()
        await self._check_system_resources()
        
        # Network checks
        await self._check_network_configuration()
        
        total_time = (time.time() - start_time) * 1000
        
        # Generate summary
        summary = self._generate_summary()
        
        return {
            "summary": summary,
            "results": [asdict(result) for result in self._results],
            "total_duration_ms": int(total_time),
            "timestamp": datetime.now().isoformat(),
            "recommendations": self._generate_recommendations()
        }
        
    async def _check_system_requirements(self) -> None:
        """Check system requirements."""
        start_time = time.time()
        
        try:
            # Check Python version
            import sys
            python_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
            
            if sys.version_info >= (3, 8):
                status = "pass"
                message = f"Python {python_version} is supported"
            else:
                status = "fail"
                message = f"Python {python_version} is too old (requires 3.8+)"
                
            self._add_result("python_version", status, message, {
                "version": python_version,
                "required": "3.8+"
            }, start_time)
            
            # Check operating system
            import platform
            os_info = {
                "system": platform.system(),
                "release": platform.release(),
                "version": platform.version(),
                "machine": platform.machine()
            }
            
            if platform.system() in ["Linux", "Darwin"]:
                status = "pass"
                message = f"Operating system {platform.system()} is supported"
            else:
                status = "warning"
                message = f"Operating system {platform.system()} may have limited support"
                
            self._add_result("operating_system", status, message, os_info, start_time)
            
        except Exception as err:
            self._add_result("system_requirements", "fail", f"Error checking system: {err}", {}, start_time)
            
    async def _check_bluetooth_stack(self) -> None:
        """Check Bluetooth stack availability."""
        start_time = time.time()
        
        try:
            # Check bluetoothctl
            result = await asyncio.create_subprocess_exec(
                "bluetoothctl", "--version",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await result.communicate()
            
            if result.returncode == 0:
                version = stdout.decode().strip()
                self._add_result("bluetoothctl", "pass", f"bluetoothctl available: {version}", {
                    "version": version,
                    "command": "bluetoothctl"
                }, start_time)
            else:
                self._add_result("bluetoothctl", "fail", "bluetoothctl not available", {
                    "error": stderr.decode().strip()
                }, start_time)
                
            # Check Bluetooth service
            result = await asyncio.create_subprocess_exec(
                "systemctl", "is-active", "bluetooth",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await result.communicate()
            
            if result.returncode == 0 and stdout.decode().strip() == "active":
                self._add_result("bluetooth_service", "pass", "Bluetooth service is active", {}, start_time)
            else:
                self._add_result("bluetooth_service", "warning", "Bluetooth service status unknown", {
                    "status": stdout.decode().strip()
                }, start_time)
                
        except Exception as err:
            self._add_result("bluetooth_stack", "fail", f"Error checking Bluetooth stack: {err}", {}, start_time)
            
    async def _check_audio_stack(self) -> None:
        """Check audio stack availability."""
        start_time = time.time()
        
        # Check GStreamer
        try:
            import gi  # type: ignore
            gi.require_version('Gst', '1.0')  # type: ignore
            from gi.repository import Gst  # type: ignore
            
            if not Gst.is_initialized():
                Gst.init(None)
                
            version = Gst.version_string()
            self._add_result("gstreamer", "pass", f"GStreamer available: {version}", {
                "version": version
            }, start_time)
            
        except ImportError:
            self._add_result("gstreamer", "fail", "GStreamer not available", {
                "error": "gi.repository.Gst not found"
            }, start_time)
        except Exception as err:
            self._add_result("gstreamer", "fail", f"GStreamer error: {err}", {}, start_time)
            
        # Check PulseAudio
        try:
            result = await asyncio.create_subprocess_exec(
                "pulseaudio", "--version",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await result.communicate()
            
            if result.returncode == 0:
                version = stdout.decode().strip()
                self._add_result("pulseaudio", "pass", f"PulseAudio available: {version}", {
                    "version": version
                }, start_time)
            else:
                self._add_result("pulseaudio", "warning", "PulseAudio not available", {}, start_time)
                
        except Exception as err:
            self._add_result("pulseaudio", "warning", f"PulseAudio check failed: {err}", {}, start_time)
            
        # Check ALSA
        try:
            result = await asyncio.create_subprocess_exec(
                "aplay", "--version",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await result.communicate()
            
            if result.returncode == 0:
                version = stdout.decode().strip().split('\n')[0]
                self._add_result("alsa", "pass", f"ALSA available: {version}", {
                    "version": version
                }, start_time)
            else:
                self._add_result("alsa", "warning", "ALSA not available", {}, start_time)
                
        except Exception as err:
            self._add_result("alsa", "warning", f"ALSA check failed: {err}", {}, start_time)
            
    async def _check_bluetooth_devices(self) -> None:
        """Check Bluetooth device availability."""
        start_time = time.time()
        
        try:
            # List Bluetooth devices
            result = await asyncio.create_subprocess_exec(
                "bluetoothctl", "devices",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await result.communicate()
            
            if result.returncode == 0:
                devices = []
                for line in stdout.decode().strip().split('\n'):
                    if line.startswith('Device '):
                        parts = line.split(' ', 2)
                        if len(parts) >= 3:
                            devices.append({
                                "address": parts[1],
                                "name": parts[2]
                            })
                            
                self._add_result("bluetooth_devices", "info", f"Found {len(devices)} Bluetooth devices", {
                    "devices": devices,
                    "count": len(devices)
                }, start_time)
            else:
                self._add_result("bluetooth_devices", "fail", "Failed to list Bluetooth devices", {
                    "error": stderr.decode().strip()
                }, start_time)
                
        except Exception as err:
            self._add_result("bluetooth_devices", "fail", f"Error checking Bluetooth devices: {err}", {}, start_time)
            
    async def _check_audio_devices(self) -> None:
        """Check audio device availability."""
        start_time = time.time()
        
        try:
            # Check PulseAudio sinks
            result = await asyncio.create_subprocess_exec(
                "pactl", "list", "short", "sinks",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await result.communicate()
            
            if result.returncode == 0:
                sinks = []
                for line in stdout.decode().strip().split('\n'):
                    if line:
                        parts = line.split('\t')
                        if len(parts) >= 2:
                            sinks.append({
                                "id": parts[0],
                                "name": parts[1]
                            })
                            
                self._add_result("audio_sinks", "info", f"Found {len(sinks)} audio sinks", {
                    "sinks": sinks,
                    "count": len(sinks)
                }, start_time)
            else:
                self._add_result("audio_sinks", "warning", "Failed to list audio sinks", {}, start_time)
                
            # Check PulseAudio sources
            result = await asyncio.create_subprocess_exec(
                "pactl", "list", "short", "sources",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await result.communicate()
            
            if result.returncode == 0:
                sources = []
                for line in stdout.decode().strip().split('\n'):
                    if line:
                        parts = line.split('\t')
                        if len(parts) >= 2:
                            sources.append({
                                "id": parts[0],
                                "name": parts[1]
                            })
                            
                self._add_result("audio_sources", "info", f"Found {len(sources)} audio sources", {
                    "sources": sources,
                    "count": len(sources)
                }, start_time)
            else:
                self._add_result("audio_sources", "warning", "Failed to list audio sources", {}, start_time)
                
        except Exception as err:
            self._add_result("audio_devices", "warning", f"Error checking audio devices: {err}", {}, start_time)
            
    async def _check_audio_configuration(self) -> None:
        """Check audio configuration."""
        start_time = time.time()
        
        try:
            # Check Bluetooth audio profiles
            result = await asyncio.create_subprocess_exec(
                "pactl", "list", "modules",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await result.communicate()
            
            if result.returncode == 0:
                output = stdout.decode()
                bluetooth_modules = []
                
                if "module-bluetooth-discover" in output:
                    bluetooth_modules.append("bluetooth-discover")
                if "module-bluez5-discover" in output:
                    bluetooth_modules.append("bluez5-discover")
                if "module-bluetooth-policy" in output:
                    bluetooth_modules.append("bluetooth-policy")
                    
                if bluetooth_modules:
                    self._add_result("bluetooth_audio_modules", "pass", 
                                   f"Bluetooth audio modules loaded: {', '.join(bluetooth_modules)}", {
                        "modules": bluetooth_modules
                    }, start_time)
                else:
                    self._add_result("bluetooth_audio_modules", "warning", 
                                   "No Bluetooth audio modules found", {}, start_time)
            else:
                self._add_result("bluetooth_audio_modules", "warning", 
                               "Failed to check PulseAudio modules", {}, start_time)
                
        except Exception as err:
            self._add_result("audio_configuration", "warning", 
                           f"Error checking audio configuration: {err}", {}, start_time)
            
    async def _check_permissions(self) -> None:
        """Check user permissions."""
        start_time = time.time()
        
        try:
            import os
            import grp
            
            # Check audio group membership
            try:
                audio_group = grp.getgrnam('audio')
                user_groups = os.getgroups()
                
                if audio_group.gr_gid in user_groups:
                    self._add_result("audio_group", "pass", "User is in audio group", {}, start_time)
                else:
                    self._add_result("audio_group", "warning", 
                                   "User not in audio group - may cause permission issues", {
                        "recommendation": "Add user to audio group: sudo usermod -a -G audio $USER"
                    }, start_time)
            except KeyError:
                self._add_result("audio_group", "info", "Audio group not found", {}, start_time)
                
            # Check Bluetooth group membership
            try:
                bluetooth_group = grp.getgrnam('bluetooth')
                user_groups = os.getgroups()
                
                if bluetooth_group.gr_gid in user_groups:
                    self._add_result("bluetooth_group", "pass", "User is in bluetooth group", {}, start_time)
                else:
                    self._add_result("bluetooth_group", "warning", 
                                   "User not in bluetooth group - may cause permission issues", {
                        "recommendation": "Add user to bluetooth group: sudo usermod -a -G bluetooth $USER"
                    }, start_time)
            except KeyError:
                self._add_result("bluetooth_group", "info", "Bluetooth group not found", {}, start_time)
                
        except Exception as err:
            self._add_result("permissions", "warning", f"Error checking permissions: {err}", {}, start_time)
            
    async def _check_audio_latency(self) -> None:
        """Check audio latency."""
        start_time = time.time()
        
        try:
            # Test audio latency with a simple pipeline
            result = await asyncio.create_subprocess_exec(
                "gst-launch-1.0", "--quiet", 
                "audiotestsrc", "num-buffers=10", "!", 
                "audioconvert", "!", 
                "fakesink",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            test_start = time.time()
            stdout, stderr = await result.communicate()
            test_duration = (time.time() - test_start) * 1000
            
            if result.returncode == 0:
                if test_duration < 1000:  # Less than 1 second
                    status = "pass"
                    message = f"Audio pipeline test completed in {test_duration:.1f}ms"
                else:
                    status = "warning"
                    message = f"Audio pipeline test slow: {test_duration:.1f}ms"
                    
                self._add_result("audio_latency", status, message, {
                    "duration_ms": test_duration
                }, start_time)
            else:
                self._add_result("audio_latency", "fail", "Audio pipeline test failed", {
                    "error": stderr.decode().strip()
                }, start_time)
                
        except Exception as err:
            self._add_result("audio_latency", "warning", f"Error testing audio latency: {err}", {}, start_time)
            
    async def _check_system_resources(self) -> None:
        """Check system resources."""
        start_time = time.time()
        
        try:
            import psutil
            
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            if cpu_percent < 80:
                status = "pass"
                message = f"CPU usage normal: {cpu_percent:.1f}%"
            else:
                status = "warning"
                message = f"High CPU usage: {cpu_percent:.1f}%"
                
            self._add_result("cpu_usage", status, message, {
                "cpu_percent": cpu_percent
            }, start_time)
            
            # Memory usage
            memory = psutil.virtual_memory()
            if memory.percent < 80:
                status = "pass"
                message = f"Memory usage normal: {memory.percent:.1f}%"
            else:
                status = "warning"
                message = f"High memory usage: {memory.percent:.1f}%"
                
            self._add_result("memory_usage", status, message, {
                "memory_percent": memory.percent,
                "available_gb": memory.available / (1024**3)
            }, start_time)
            
        except ImportError:
            self._add_result("system_resources", "info", "psutil not available for resource monitoring", {}, start_time)
        except Exception as err:
            self._add_result("system_resources", "warning", f"Error checking system resources: {err}", {}, start_time)
            
    async def _check_network_configuration(self) -> None:
        """Check network configuration for AirPlay."""
        start_time = time.time()
        
        try:
            # Check if mDNS is available
            result = await asyncio.create_subprocess_exec(
                "avahi-browse", "--version",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await result.communicate()
            
            if result.returncode == 0:
                self._add_result("mdns_avahi", "pass", "Avahi mDNS available", {}, start_time)
            else:
                # Try systemd-resolved
                result = await asyncio.create_subprocess_exec(
                    "systemd-resolve", "--version",
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                stdout, stderr = await result.communicate()
                
                if result.returncode == 0:
                    self._add_result("mdns_systemd", "pass", "systemd-resolved mDNS available", {}, start_time)
                else:
                    self._add_result("mdns", "warning", "No mDNS service found", {
                        "recommendation": "Install avahi-daemon or enable systemd-resolved"
                    }, start_time)
                    
        except Exception as err:
            self._add_result("network_configuration", "warning", f"Error checking network: {err}", {}, start_time)
            
    def _add_result(self, test_name: str, status: str, message: str, 
                   details: Dict[str, Any], start_time: float) -> None:
        """Add a diagnostic result."""
        duration_ms = int((time.time() - start_time) * 1000)
        
        result = AudioDiagnosticResult(
            test_name=test_name,
            status=status,
            message=message,
            details=details,
            timestamp=datetime.now().isoformat(),
            duration_ms=duration_ms
        )
        
        self._results.append(result)
        _LOGGER.debug("Diagnostic result: %s - %s", test_name, status)
        
    def _generate_summary(self) -> Dict[str, Any]:
        """Generate diagnostic summary."""
        total_tests = len(self._results)
        passed = sum(1 for r in self._results if r.status == "pass")
        failed = sum(1 for r in self._results if r.status == "fail")
        warnings = sum(1 for r in self._results if r.status == "warning")
        info = sum(1 for r in self._results if r.status == "info")
        
        overall_status = "pass"
        if failed > 0:
            overall_status = "fail"
        elif warnings > 0:
            overall_status = "warning"
            
        return {
            "overall_status": overall_status,
            "total_tests": total_tests,
            "passed": passed,
            "failed": failed,
            "warnings": warnings,
            "info": info,
            "success_rate": (passed / total_tests * 100) if total_tests > 0 else 0
        }
        
    def _generate_recommendations(self) -> List[Dict[str, Any]]:
        """Generate recommendations based on diagnostic results."""
        recommendations = []
        
        # Check for common issues and provide recommendations
        for result in self._results:
            if result.status == "fail":
                if result.test_name == "bluetoothctl":
                    recommendations.append({
                        "priority": "high",
                        "category": "bluetooth",
                        "issue": "bluetoothctl not available",
                        "solution": "Install bluez package: sudo apt-get install bluez",
                        "commands": ["sudo apt-get update", "sudo apt-get install bluez"]
                    })
                elif result.test_name == "gstreamer":
                    recommendations.append({
                        "priority": "high",
                        "category": "audio",
                        "issue": "GStreamer not available",
                        "solution": "Install GStreamer: sudo apt-get install gstreamer1.0-tools gstreamer1.0-plugins-base",
                        "commands": ["sudo apt-get install gstreamer1.0-tools gstreamer1.0-plugins-base gstreamer1.0-plugins-good"]
                    })
            elif result.status == "warning":
                if "group" in result.test_name and "recommendation" in result.details:
                    recommendations.append({
                        "priority": "medium",
                        "category": "permissions",
                        "issue": f"User not in {result.test_name.replace('_group', '')} group",
                        "solution": result.details["recommendation"],
                        "commands": [result.details["recommendation"]]
                    })
                    
        return recommendations
        
    async def test_bluetooth_connection(self, device_address: str) -> Dict[str, Any]:
        """Test Bluetooth connection to specific device."""
        start_time = time.time()
        
        try:
            # Test connection
            result = await asyncio.create_subprocess_exec(
                "bluetoothctl", "connect", device_address,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await result.communicate()
            
            success = result.returncode == 0 and "successful" in stdout.decode().lower()
            
            return {
                "device_address": device_address,
                "connection_successful": success,
                "output": stdout.decode(),
                "error": stderr.decode(),
                "duration_ms": int((time.time() - start_time) * 1000)
            }
            
        except Exception as err:
            return {
                "device_address": device_address,
                "connection_successful": False,
                "error": str(err),
                "duration_ms": int((time.time() - start_time) * 1000)
            }
            
    async def test_audio_pipeline(self, codec: str = "sbc") -> Dict[str, Any]:
        """Test audio pipeline with specific codec."""
        start_time = time.time()
        
        try:
            # Create test pipeline
            pipeline_cmd = [
                "gst-launch-1.0", "--quiet",
                "audiotestsrc", "num-buffers=100", "freq=440", "!",
                "audioconvert", "!",
                f"audio/x-raw,rate=44100,channels=2", "!",
                "fakesink"
            ]
            
            result = await asyncio.create_subprocess_exec(
                *pipeline_cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await result.communicate()
            
            success = result.returncode == 0
            
            return {
                "codec": codec,
                "pipeline_successful": success,
                "output": stdout.decode(),
                "error": stderr.decode(),
                "duration_ms": int((time.time() - start_time) * 1000)
            }
            
        except Exception as err:
            return {
                "codec": codec,
                "pipeline_successful": False,
                "error": str(err),
                "duration_ms": int((time.time() - start_time) * 1000)
            }


# Global diagnostics instance
audio_diagnostics = AudioDiagnostics()