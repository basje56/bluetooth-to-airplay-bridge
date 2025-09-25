"""AirPlay server implementation for Bluetooth to AirPlay Bridge."""
from __future__ import annotations

import asyncio
import json
import logging
import socket
import struct
import time
from typing import Any, Optional, Dict, Callable
from datetime import datetime

try:
    import aiohttp
    from aiohttp import web
    AIOHTTP_AVAILABLE = True
except ImportError:
    AIOHTTP_AVAILABLE = False
    web = None

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

class AirPlayServer:
    """Pure Python async AirPlay server implementation."""
    
    def __init__(self, name: str, port: int = 5000) -> None:
        """Initialize AirPlay server."""
        self._name = name
        self._port = port
        self._server: Optional[web.TCPSite] = None
        self._app: Optional[web.Application] = None
        self._is_running = False
        self._volume = 50.0
        self._metadata_callback: Optional[Callable] = None
        self._current_metadata: Dict[str, Any] = {}
        self._session_id: Optional[str] = None
        self._audio_format: Dict[str, Any] = {
            "type": 96,
            "channels": 2,
            "sample_rate": 44100,
            "sample_size": 16
        }
        
        if not AIOHTTP_AVAILABLE:
            _LOGGER.error("aiohttp not available - AirPlay server will not work")
        
    async def start(self) -> bool:
        """Start the AirPlay server."""
        try:
            if not AIOHTTP_AVAILABLE:
                _LOGGER.error("aiohttp not available - cannot start AirPlay server")
                return False
                
            if self._is_running:
                _LOGGER.warning("AirPlay server is already running")
                return True
                
            # Create aiohttp application
            self._app = web.Application()
            
            # Setup AirPlay routes
            self._setup_routes()
            
            # Create and start the server
            runner = web.AppRunner(self._app)
            await runner.setup()
            
            self._server = web.TCPSite(runner, '0.0.0.0', self._port)
            await self._server.start()
            
            self._is_running = True
            self._session_id = f"airplay_{int(time.time())}"
            
            _LOGGER.info("AirPlay server started on port %d as '%s'", self._port, self._name)
            return True
            
        except Exception as err:
            _LOGGER.error("Error starting AirPlay server: %s", err)
            return False
            
    async def stop(self) -> None:
        """Stop the AirPlay server."""
        try:
            if not self._is_running:
                return
                
            _LOGGER.info("Stopping AirPlay server...")
            
            # Stop the server
            if self._server:
                await self._server.stop()
                self._server = None
                
            # Cleanup the app
            if self._app:
                await self._app.cleanup()
                self._app = None
                
            self._is_running = False
            self._session_id = None
            self._current_metadata.clear()
            
            _LOGGER.info("AirPlay server stopped")
            
        except Exception as err:
            _LOGGER.error("Error stopping AirPlay server: %s", err)
            
    def _setup_routes(self) -> None:
        """Setup AirPlay HTTP routes."""
        if not self._app:
            return
            
        # AirPlay discovery and info endpoints
        self._app.router.add_get('/info', self._handle_info)
        self._app.router.add_post('/pair-setup', self._handle_pair_setup)
        self._app.router.add_post('/pair-verify', self._handle_pair_verify)
        
        # Audio streaming endpoints
        self._app.router.add_post('/audio', self._handle_audio)
        self._app.router.add_get('/stream.wav', self._handle_audio_stream)
        
        # Control endpoints
        self._app.router.add_post('/volume', self._handle_volume)
        self._app.router.add_post('/play', self._handle_play)
        self._app.router.add_post('/pause', self._handle_pause)
        self._app.router.add_post('/stop', self._handle_stop)
        
        # Metadata endpoints
        self._app.router.add_post('/setProperty', self._handle_set_property)
        self._app.router.add_get('/getProperty', self._handle_get_property)
        
        _LOGGER.debug("AirPlay routes configured")
        
    async def _handle_info(self, request: web.Request) -> web.Response:
        """Handle AirPlay info request."""
        info = {
            "name": self._name,
            "deviceid": "AA:BB:CC:DD:EE:FF",  # Mock device ID
            "features": "0x445F8A00,0x1C340",  # AirPlay features
            "model": "AppleTV3,2",
            "protovers": "1.0",
            "srcvers": "220.68",
            "pi": "b08f5a79-db29-4384-b456-a4784d9e6055",  # Mock UUID
            "pk": "99d0c7c8d184c3e8c4f0dcef7e711a7c",  # Mock public key
            "vv": "2"
        }
        return web.Response(
            text="\r\n".join(f"{k}: {v}" for k, v in info.items()) + "\r\n",
            content_type="text/plain"
        )
        
    async def _handle_pair_setup(self, request: web.Request) -> web.Response:
        """Handle AirPlay pair setup request."""
        # Simple mock pairing response
        return web.Response(
            body=b'\x01\x00',  # Mock pairing response
            content_type="application/octet-stream"
        )
        
    async def _handle_pair_verify(self, request: web.Request) -> web.Response:
        """Handle AirPlay pair verify request."""
        # Simple mock verification response
        return web.Response(
            body=b'\x00\x00',  # Mock verification response
            content_type="application/octet-stream"
        )
        
    async def _handle_audio(self, request: web.Request) -> web.Response:
        """Handle audio data from AirPlay client."""
        try:
            # Read audio data
            audio_data = await request.read()
            _LOGGER.debug("Received %d bytes of audio data", len(audio_data))
            
            # Store current audio format if provided in headers
            if 'Content-Type' in request.headers:
                self._audio_format = request.headers['Content-Type']
                
            # Here we would process the audio data
            # For now, just acknowledge receipt
            return web.Response(status=200)
            
        except Exception as err:
            _LOGGER.error("Error handling audio data: %s", err)
            return web.Response(status=500)
            
    async def _handle_audio_stream(self, request: web.Request) -> web.Response:
        """Handle audio stream request."""
        # Return a simple audio stream response
        return web.Response(
            body=b'',  # Empty audio stream for now
            content_type="audio/wav"
        )
        
    async def _handle_volume(self, request: web.Request) -> web.Response:
        """Handle volume control request."""
        try:
            data = await request.read()
            # Parse volume data (simplified)
            if data:
                volume = struct.unpack('>f', data[:4])[0] if len(data) >= 4 else 0.5
                self._volume = max(0.0, min(1.0, volume))
                _LOGGER.debug("Volume set to: %f", self._volume)
                
            return web.Response(status=200)
            
        except Exception as err:
            _LOGGER.error("Error handling volume: %s", err)
            return web.Response(status=500)
            
    async def _handle_play(self, request: web.Request) -> web.Response:
        """Handle play request."""
        _LOGGER.debug("Play command received")
        return web.Response(status=200)
        
    async def _handle_pause(self, request: web.Request) -> web.Response:
        """Handle pause request."""
        _LOGGER.debug("Pause command received")
        return web.Response(status=200)
        
    async def _handle_stop(self, request: web.Request) -> web.Response:
        """Handle stop request."""
        _LOGGER.debug("Stop command received")
        self._current_metadata.clear()
        return web.Response(status=200)
        
    async def _handle_set_property(self, request: web.Request) -> web.Response:
        """Handle set property request."""
        try:
            data = await request.text()
            _LOGGER.debug("Set property: %s", data)
            
            # Parse and store metadata
            if "title" in data.lower():
                self._current_metadata["title"] = data
            elif "artist" in data.lower():
                self._current_metadata["artist"] = data
            elif "album" in data.lower():
                self._current_metadata["album"] = data
                
            return web.Response(status=200)
            
        except Exception as err:
            _LOGGER.error("Error setting property: %s", err)
            return web.Response(status=500)
            
    async def _handle_get_property(self, request: web.Request) -> web.Response:
        """Handle get property request."""
        # Return current metadata as properties
        return web.Response(
            text=json.dumps(self._current_metadata),
            content_type="application/json"
        )
            
    async def set_volume(self, volume: int) -> bool:
        """Set AirPlay server volume (0-100)."""
        try:
            if not 0 <= volume <= 100:
                _LOGGER.error("Invalid volume level: %d", volume)
                return False
                
            self._volume = volume / 100.0  # Store as float 0.0-1.0
            _LOGGER.info("Volume set to %d%%", volume)
            return True
            
        except Exception as err:
            _LOGGER.error("Error setting volume: %s", err)
            return False
    
    def get_volume(self) -> float:
        """Get current AirPlay server volume (0.0-1.0)."""
        return self._volume
    
    def set_volume_float(self, volume: float) -> None:
        """Set AirPlay server volume using float (0.0-1.0)."""
        self._volume = max(0.0, min(1.0, volume))
            
    async def get_status(self) -> dict[str, Any]:
        """Get AirPlay server status."""
        return {
            "running": self._is_running,
            "name": self._name,
            "port": self._port,
            "volume": int(self._volume * 100),
            "session_id": self._session_id,
            "audio_format": self._audio_format,
            "metadata": self._current_metadata.copy(),
        }
        
    async def get_metadata(self) -> Optional[dict[str, Any]]:
        """Get current playing metadata from AirPlay."""
        try:
            if not self._is_running:
                return None
                
            # Return current metadata stored from AirPlay clients
            metadata = self._current_metadata.copy()
            metadata.update({
                "playing": self._is_running,
                "volume": int(self._volume * 100),
                "session_id": self._session_id,
                "timestamp": datetime.now().isoformat()
            })
            
            return metadata if metadata else None
            
        except Exception as err:
            _LOGGER.error("Error getting metadata: %s", err)
            return None
            
    def set_metadata_callback(self, callback: callable) -> None:
        """Set callback for metadata updates."""
        self._metadata_callback = callback
        
    @property
    def is_running(self) -> bool:
        """Check if AirPlay server is running."""
        return self._is_running
        
    @property
    def name(self) -> str:
        """Get AirPlay server name."""
        return self._name
        
    @property
    def port(self) -> int:
        """Get AirPlay server port."""
        return self._port