"""AirPlay receiver discovery for automatic network detection."""
from __future__ import annotations

import asyncio
import logging
import socket
from datetime import datetime, timedelta
from typing import Any, Callable, Optional

try:
    from zeroconf import ServiceBrowser, ServiceListener, Zeroconf  # type: ignore
    from zeroconf.asyncio import AsyncZeroconf, AsyncServiceBrowser  # type: ignore
    ZEROCONF_AVAILABLE = True
except ImportError:
    ZEROCONF_AVAILABLE = False
    # Create dummy classes for type checking
    class ServiceListener:  # type: ignore
        pass
    class Zeroconf:  # type: ignore
        pass
    class AsyncZeroconf:  # type: ignore
        pass
    class AsyncServiceBrowser:  # type: ignore
        pass

from homeassistant.core import HomeAssistant  # type: ignore

_LOGGER = logging.getLogger(__name__)

class AirPlayReceiver:
    """Represents a discovered AirPlay receiver."""
    
    def __init__(self, name: str, address: str, port: int, properties: dict[str, Any]) -> None:
        """Initialize AirPlay receiver."""
        self.name = name
        self.address = address
        self.port = port
        self.properties = properties
        self.discovered_at = datetime.now()
        self.last_seen = datetime.now()
        
    @property
    def is_airplay2(self) -> bool:
        """Check if this is an AirPlay 2 device."""
        features = self.properties.get("features", "")
        # AirPlay 2 devices typically have specific feature flags
        return "0x48F" in str(features) or "0x5A7FFFF7" in str(features)
        
    @property
    def supports_audio(self) -> bool:
        """Check if device supports audio streaming."""
        features = self.properties.get("features", "")
        # Check for audio support flag (bit 0)
        try:
            feature_int = int(features, 16) if isinstance(features, str) else features
            return bool(feature_int & 0x1)
        except (ValueError, TypeError):
            return True  # Assume audio support if we can't parse features
            
    @property
    def device_model(self) -> str:
        """Get device model information."""
        return self.properties.get("model", "Unknown AirPlay Device")
        
    def to_dict(self) -> dict[str, Any]:
        """Convert receiver to dictionary."""
        return {
            "name": self.name,
            "address": self.address,
            "port": self.port,
            "is_airplay2": self.is_airplay2,
            "supports_audio": self.supports_audio,
            "device_model": self.device_model,
            "discovered_at": self.discovered_at.isoformat(),
            "last_seen": self.last_seen.isoformat(),
            "properties": self.properties
        }
        
    def __str__(self) -> str:
        """String representation of receiver."""
        return f"{self.name} ({self.address}:{self.port}) - {self.device_model}"

class AirPlayServiceListener:
    """Service listener for AirPlay device discovery."""
    
    def __init__(self, discovery_manager: AirPlayDiscoveryManager) -> None:
        """Initialize service listener."""
        self._discovery_manager = discovery_manager
        
    def add_service(self, zc: Any, type_: str, name: str) -> None:
        """Called when a service is discovered."""
        asyncio.create_task(self._discovery_manager._handle_service_added(zc, type_, name))
        
    def remove_service(self, zc: Any, type_: str, name: str) -> None:
        """Called when a service is removed."""
        asyncio.create_task(self._discovery_manager._handle_service_removed(zc, type_, name))
        
    def update_service(self, zc: Any, type_: str, name: str) -> None:
        """Called when a service is updated."""
        asyncio.create_task(self._discovery_manager._handle_service_updated(zc, type_, name))

class AirPlayDiscoveryManager:
    """Manages discovery of AirPlay receivers on the local network."""
    
    def __init__(self, hass: HomeAssistant) -> None:
        """Initialize AirPlay discovery manager."""
        self._hass = hass
        self._receivers: dict[str, AirPlayReceiver] = {}
        self._zeroconf: Optional[Any] = None
        self._browser: Optional[Any] = None
        self._listener: Optional[AirPlayServiceListener] = None
        self._is_discovering = False
        self._discovery_callbacks: list[Callable[[dict[str, AirPlayReceiver]], None]] = []
        self._receiver_callbacks: list[Callable[[AirPlayReceiver, str], None]] = []  # receiver, action (added/removed/updated)
        
        # AirPlay service types to discover
        self._service_types = [
            "_raop._tcp.local.",  # AirPlay audio
            "_airplay._tcp.local.",  # AirPlay 2
        ]
        
        if not ZEROCONF_AVAILABLE:
            _LOGGER.error("Zeroconf not available - AirPlay discovery will not work")
            
    @property
    def receivers(self) -> dict[str, AirPlayReceiver]:
        """Get all discovered receivers."""
        return self._receivers.copy()
        
    @property
    def airplay2_receivers(self) -> list[AirPlayReceiver]:
        """Get AirPlay 2 receivers only."""
        return [receiver for receiver in self._receivers.values() if receiver.is_airplay2]
        
    @property
    def audio_receivers(self) -> list[AirPlayReceiver]:
        """Get audio-capable receivers."""
        return [receiver for receiver in self._receivers.values() if receiver.supports_audio]
        
    @property
    def is_discovering(self) -> bool:
        """Check if discovery is active."""
        return self._is_discovering
        
    def add_discovery_callback(self, callback: Callable[[dict[str, AirPlayReceiver]], None]) -> None:
        """Add callback for receiver list updates."""
        self._discovery_callbacks.append(callback)
        
    def add_receiver_callback(self, callback: Callable[[AirPlayReceiver, str], None]) -> None:
        """Add callback for individual receiver updates."""
        self._receiver_callbacks.append(callback)
        
    def remove_discovery_callback(self, callback: Callable[[dict[str, AirPlayReceiver]], None]) -> None:
        """Remove discovery callback."""
        if callback in self._discovery_callbacks:
            self._discovery_callbacks.remove(callback)
            
    def remove_receiver_callback(self, callback: Callable[[AirPlayReceiver, str], None]) -> None:
        """Remove receiver callback."""
        if callback in self._receiver_callbacks:
            self._receiver_callbacks.remove(callback)
            
    async def start_discovery(self) -> bool:
        """Start AirPlay receiver discovery."""
        if not ZEROCONF_AVAILABLE:
            _LOGGER.error("Cannot start AirPlay discovery - zeroconf not available")
            return False
            
        if self._is_discovering:
            _LOGGER.debug("AirPlay discovery already running")
            return True
            
        try:
            _LOGGER.info("Starting AirPlay receiver discovery")
            
            # Create AsyncZeroconf instance
            self._zeroconf = AsyncZeroconf()
            
            # Create service listener
            self._listener = AirPlayServiceListener(self)
            
            # Start browsing for each service type
            browsers = []
            for service_type in self._service_types:
                if hasattr(self._zeroconf, 'zeroconf') and ZEROCONF_AVAILABLE:
                    browser = AsyncServiceBrowser(
                        self._zeroconf.zeroconf,
                        service_type,
                        handlers=[self._listener]
                    )
                    browsers.append(browser)
                
            self._browser = browsers[0] if browsers else None  # Store first browser for reference
            self._is_discovering = True
            
            _LOGGER.info("AirPlay discovery started, monitoring %d service types", len(self._service_types))
            return True
            
        except Exception as err:
            _LOGGER.error("Error starting AirPlay discovery: %s", err)
            await self.stop_discovery()
            return False
            
    async def stop_discovery(self) -> None:
        """Stop AirPlay receiver discovery."""
        if not self._is_discovering:
            return
            
        try:
            _LOGGER.info("Stopping AirPlay receiver discovery")
            
            # Close zeroconf
            if self._zeroconf and hasattr(self._zeroconf, 'async_close'):
                await self._zeroconf.async_close()
                self._zeroconf = None
                
            self._browser = None
            self._listener = None
            self._is_discovering = False
            
            _LOGGER.info("AirPlay discovery stopped")
            
        except Exception as err:
            _LOGGER.error("Error stopping AirPlay discovery: %s", err)
            
    async def refresh_discovery(self) -> None:
        """Refresh discovery by restarting it."""
        if self._is_discovering:
            await self.stop_discovery()
            await asyncio.sleep(1)  # Brief pause
        await self.start_discovery()
        
    async def _handle_service_added(self, zc: Any, type_: str, name: str) -> None:
        """Handle discovered AirPlay service."""
        try:
            if not hasattr(zc, 'get_service_info'):
                return
            info = zc.get_service_info(type_, name)
            if not info:
                return
                
            # Extract receiver information
            receiver = self._create_receiver_from_service_info(info, type_)
            if receiver:
                # Use service name as unique key
                service_key = f"{name}_{type_}"
                self._receivers[service_key] = receiver
                
                _LOGGER.info("Discovered AirPlay receiver: %s", receiver)
                
                # Notify callbacks
                self._notify_receiver_callbacks(receiver, "added")
                self._notify_discovery_callbacks()
                
        except Exception as err:
            _LOGGER.error("Error handling service addition for %s: %s", name, err)
            
    async def _handle_service_removed(self, zc: Zeroconf, type_: str, name: str) -> None:
        """Handle removed AirPlay service."""
        try:
            service_key = f"{name}_{type_}"
            if service_key in self._receivers:
                receiver = self._receivers.pop(service_key)
                _LOGGER.info("AirPlay receiver removed: %s", receiver)
                
                # Notify callbacks
                self._notify_receiver_callbacks(receiver, "removed")
                self._notify_discovery_callbacks()
                
        except Exception as err:
            _LOGGER.error("Error handling service removal for %s: %s", name, err)
            
    async def _handle_service_updated(self, zc: Any, type_: str, name: str) -> None:
        """Handle updated AirPlay service."""
        try:
            if not hasattr(zc, 'get_service_info'):
                return
            info = zc.get_service_info(type_, name)
            if not info:
                return
                
            service_key = f"{name}_{type_}"
            receiver = self._create_receiver_from_service_info(info, type_)
            
            if receiver:
                # Update last seen time if receiver already exists
                if service_key in self._receivers:
                    receiver.last_seen = datetime.now()
                    
                self._receivers[service_key] = receiver
                
                _LOGGER.debug("AirPlay receiver updated: %s", receiver)
                
                # Notify callbacks
                self._notify_receiver_callbacks(receiver, "updated")
                self._notify_discovery_callbacks()
                
        except Exception as err:
            _LOGGER.error("Error handling service update for %s: %s", name, err)
            
    def _create_receiver_from_service_info(self, info, service_type: str) -> Optional[AirPlayReceiver]:
        """Create AirPlayReceiver from service info."""
        try:
            # Get service name (remove service type suffix)
            name = info.name.replace(f".{service_type}", "")
            
            # Get IP address
            if info.addresses:
                address = socket.inet_ntoa(info.addresses[0])
            else:
                _LOGGER.warning("No address found for service %s", info.name)
                return None
                
            # Get port
            port = info.port
            
            # Parse properties
            properties = {}
            if info.properties:
                for key, value in info.properties.items():
                    try:
                        # Decode bytes to string
                        key_str = key.decode('utf-8') if isinstance(key, bytes) else str(key)
                        value_str = value.decode('utf-8') if isinstance(value, bytes) else str(value)
                        properties[key_str] = value_str
                    except (UnicodeDecodeError, AttributeError):
                        # Keep as bytes if decoding fails
                        properties[key] = value
                        
            return AirPlayReceiver(name, address, port, properties)
            
        except Exception as err:
            _LOGGER.error("Error creating receiver from service info: %s", err)
            return None
            
    def _notify_discovery_callbacks(self) -> None:
        """Notify all discovery callbacks."""
        for callback in self._discovery_callbacks:
            try:
                callback(self._receivers.copy())
            except Exception as err:
                _LOGGER.error("Error in discovery callback: %s", err)
                
    def _notify_receiver_callbacks(self, receiver: AirPlayReceiver, action: str) -> None:
        """Notify all receiver callbacks."""
        for callback in self._receiver_callbacks:
            try:
                callback(receiver, action)
            except Exception as err:
                _LOGGER.error("Error in receiver callback: %s", err)
                
    async def get_receiver_details(self, address: str, port: int) -> Optional[dict[str, Any]]:
        """Get detailed information about a specific receiver."""
        try:
            # Find receiver by address and port
            for receiver in self._receivers.values():
                if receiver.address == address and receiver.port == port:
                    return receiver.to_dict()
            return None
            
        except Exception as err:
            _LOGGER.error("Error getting receiver details for %s:%d: %s", address, port, err)
            return None
            
    def cleanup_stale_receivers(self, max_age_minutes: int = 30) -> None:
        """Remove receivers that haven't been seen recently."""
        try:
            cutoff_time = datetime.now() - timedelta(minutes=max_age_minutes)
            stale_keys = []
            
            for key, receiver in self._receivers.items():
                if receiver.last_seen < cutoff_time:
                    stale_keys.append(key)
                    
            for key in stale_keys:
                receiver = self._receivers.pop(key)
                _LOGGER.info("Removed stale AirPlay receiver: %s", receiver)
                self._notify_receiver_callbacks(receiver, "removed")
                
            if stale_keys:
                self._notify_discovery_callbacks()
                
        except Exception as err:
            _LOGGER.error("Error cleaning up stale receivers: %s", err)