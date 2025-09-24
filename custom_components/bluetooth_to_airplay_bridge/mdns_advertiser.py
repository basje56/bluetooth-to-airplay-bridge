"""mDNS service advertisement for AirPlay discovery."""
from __future__ import annotations

import asyncio
import logging
import socket
from typing import Any, Optional

try:
    from zeroconf import ServiceInfo, Zeroconf
    from zeroconf.asyncio import AsyncZeroconf
    ZEROCONF_AVAILABLE = True
except ImportError:
    ZEROCONF_AVAILABLE = False
    ServiceInfo = None
    Zeroconf = None
    AsyncZeroconf = None

_LOGGER = logging.getLogger(__name__)

class mDNSAdvertiser:
    """Handles mDNS service advertisement for AirPlay discovery."""
    
    def __init__(self, service_name: str, port: int, version: str = "1") -> None:
        """Initialize mDNS advertiser."""
        self._service_name = service_name
        self._port = port
        self._version = version
        self._zeroconf: Optional[AsyncZeroconf] = None
        self._service_info: Optional[ServiceInfo] = None
        self._is_advertising = False
        
        if not ZEROCONF_AVAILABLE:
            _LOGGER.error("Zeroconf not available - mDNS advertising will not work")
            
    async def start_advertising(self) -> bool:
        """Start advertising AirPlay service via mDNS."""
        if not ZEROCONF_AVAILABLE:
            _LOGGER.error("Cannot start mDNS advertising - zeroconf not available")
            return False
            
        try:
            # Create AsyncZeroconf instance
            self._zeroconf = AsyncZeroconf()
            
            # Get local IP address
            local_ip = self._get_local_ip()
            if not local_ip:
                _LOGGER.error("Could not determine local IP address")
                return False
                
            # Create service info
            self._service_info = self._create_service_info(local_ip)
            if not self._service_info:
                return False
                
            # Register the service
            await self._zeroconf.async_register_service(self._service_info)
            self._is_advertising = True
            
            _LOGGER.info("Started mDNS advertising for '%s' on %s:%d", 
                        self._service_name, local_ip, self._port)
            return True
            
        except Exception as err:
            _LOGGER.error("Error starting mDNS advertising: %s", err)
            return False
            
    async def stop_advertising(self) -> None:
        """Stop mDNS advertising."""
        try:
            if self._zeroconf and self._service_info and self._is_advertising:
                await self._zeroconf.async_unregister_service(self._service_info)
                await self._zeroconf.async_close()
                
            self._is_advertising = False
            self._zeroconf = None
            self._service_info = None
            
            _LOGGER.info("Stopped mDNS advertising")
            
        except Exception as err:
            _LOGGER.error("Error stopping mDNS advertising: %s", err)
            
    def _get_local_ip(self) -> Optional[str]:
        """Get the local IP address."""
        try:
            # Connect to a remote address to determine local IP
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                s.connect(("8.8.8.8", 80))
                return s.getsockname()[0]
        except Exception:
            try:
                # Fallback: get hostname IP
                return socket.gethostbyname(socket.gethostname())
            except Exception:
                return None
                
    def _create_service_info(self, local_ip: str) -> Optional[ServiceInfo]:
        """Create ServiceInfo for AirPlay service."""
        try:
            # AirPlay service type
            service_type = "_raop._tcp.local."
            
            # Service name (must be unique)
            service_name = f"{self._service_name}.{service_type}"
            
            # TXT record properties for AirPlay
            properties = self._create_txt_properties()
            
            # Create service info
            service_info = ServiceInfo(
                type_=service_type,
                name=service_name,
                addresses=[socket.inet_aton(local_ip)],
                port=self._port,
                properties=properties,
                server=f"{self._service_name.replace(' ', '-').lower()}.local."
            )
            
            _LOGGER.debug("Created service info: %s", service_info)
            return service_info
            
        except Exception as err:
            _LOGGER.error("Error creating service info: %s", err)
            return None
            
    def _create_txt_properties(self) -> dict[bytes, bytes]:
        """Create TXT record properties for AirPlay service."""
        # Standard AirPlay TXT record properties
        properties = {
            b"txtvers": b"1",
            b"ch": b"2",  # Channels (stereo)
            b"cn": b"0,1",  # Codec numbers (PCM, ALAC)
            b"et": b"0,1",  # Encryption types
            b"sv": b"false",  # Password required
            b"tp": b"UDP",  # Transport protocol
            b"sm": b"false",  # Supports metadata
            b"ss": b"16",  # Sample size
            b"sr": b"44100",  # Sample rate
            b"pw": b"false",  # Password protected
            b"vn": b"3",  # Version number
            b"da": b"true",  # Device available
            b"md": b"0,1,2",  # Metadata types
            b"am": b"ShairportSync",  # Audio model
            b"vs": b"366.0",  # Version string
            b"ft": b"0x5A7FFFF7,0xE",  # Feature flags
        }
        
        # Add version-specific properties
        if self._version == "2":
            properties.update({
                b"pk": b"b07727d6f6cd6e08b58ede525ec3cdeaa252ad9f683feb212ef8a205246554e7",
                b"sf": b"0x4",  # Status flags for AirPlay 2
            })
            
        return properties
        
    async def update_service(self, new_name: Optional[str] = None, 
                           new_port: Optional[int] = None) -> bool:
        """Update the advertised service."""
        try:
            if not self._is_advertising:
                return False
                
            # Stop current advertising
            await self.stop_advertising()
            
            # Update parameters
            if new_name:
                self._service_name = new_name
            if new_port:
                self._port = new_port
                
            # Restart advertising
            return await self.start_advertising()
            
        except Exception as err:
            _LOGGER.error("Error updating service: %s", err)
            return False
            
    def get_status(self) -> dict[str, Any]:
        """Get mDNS advertising status."""
        return {
            "service_name": self._service_name,
            "port": self._port,
            "version": self._version,
            "is_advertising": self._is_advertising,
            "zeroconf_available": ZEROCONF_AVAILABLE
        }
        
    @property
    def is_advertising(self) -> bool:
        """Check if currently advertising."""
        return self._is_advertising
        
    @property
    def service_name(self) -> str:
        """Get service name."""
        return self._service_name