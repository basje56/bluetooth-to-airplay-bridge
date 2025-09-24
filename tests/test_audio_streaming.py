"""Test audio streaming functionality for Bluetooth to AirPlay Bridge."""
from unittest.mock import AsyncMock, MagicMock, patch
import pytest  # type: ignore
from homeassistant.config_entries import ConfigEntry  # type: ignore
from homeassistant.core import HomeAssistant  # type: ignore

from custom_components.bluetooth_to_airplay_bridge import BluetoothAirPlayCoordinator
from custom_components.bluetooth_to_airplay_bridge.audio_config import (
    AudioConfigManager,
    AudioQuality,
    AudioCodec,
    SampleRate,
    BitDepth,
    AudioSettings
)
from custom_components.bluetooth_to_airplay_bridge.audio_diagnostics import AudioDiagnostics
from custom_components.bluetooth_to_airplay_bridge.const import (
    CONF_AIRPLAY_NAME,
    CONF_AIRPLAY_VERSION,
    CONF_BLUETOOTH_ADDRESS,
    CONF_BLUETOOTH_NAME,
    DOMAIN,
)


@pytest.fixture
def mock_config_entry():
    """Mock config entry."""
    return ConfigEntry(
        version=1,
        minor_version=1,
        domain=DOMAIN,
        title="Test AirPlay Bridge",
        data={
            CONF_BLUETOOTH_ADDRESS: "AA:BB:CC:DD:EE:FF",
            CONF_BLUETOOTH_NAME: "Test Speaker",
            CONF_AIRPLAY_NAME: "Test AirPlay",
            CONF_AIRPLAY_VERSION: "airplay2",
        },
        source="user",
        entry_id="test_entry_id",
        unique_id="AA:BB:CC:DD:EE:FF",
    )


@pytest.fixture
def audio_config_manager():
    """Create audio configuration manager."""
    return AudioConfigManager()


@pytest.fixture
def audio_diagnostics():
    """Create audio diagnostics."""
    return AudioDiagnostics()


class TestAudioConfigManager:
    """Test audio configuration manager."""
    
    def test_initialization(self, audio_config_manager):
        """Test audio config manager initialization."""
        assert audio_config_manager.current_settings.quality == AudioQuality.MEDIUM
        assert audio_config_manager.current_settings.codec == AudioCodec.SBC
        assert audio_config_manager.current_settings.sample_rate == SampleRate.RATE_44100
        
    def test_quality_presets(self, audio_config_manager):
        """Test quality presets."""
        # Test low quality
        success = audio_config_manager.set_quality_preset(AudioQuality.LOW)
        assert success
        assert audio_config_manager.current_settings.quality == AudioQuality.LOW
        assert audio_config_manager.current_settings.bitrate == 128000
        
        # Test high quality
        success = audio_config_manager.set_quality_preset(AudioQuality.HIGH)
        assert success
        assert audio_config_manager.current_settings.quality == AudioQuality.HIGH
        assert audio_config_manager.current_settings.codec == AudioCodec.AAC
        
        # Test lossless quality
        success = audio_config_manager.set_quality_preset(AudioQuality.LOSSLESS)
        assert success
        assert audio_config_manager.current_settings.quality == AudioQuality.LOSSLESS
        assert audio_config_manager.current_settings.codec == AudioCodec.LDAC
        
    def test_codec_detection(self, audio_config_manager):
        """Test codec detection."""
        device_info = {
            "supported_codecs": ["sbc", "aac", "aptx"]
        }
        
        audio_config_manager.detect_device_capabilities(device_info)
        supported = audio_config_manager.supported_codecs
        
        assert AudioCodec.SBC in supported
        assert AudioCodec.AAC in supported
        assert AudioCodec.APTX in supported
        assert AudioCodec.LDAC not in supported
        
    def test_optimal_settings(self, audio_config_manager):
        """Test optimal settings calculation."""
        # Set up device with limited capabilities
        device_info = {
            "supported_codecs": ["sbc", "aac"]
        }
        audio_config_manager.detect_device_capabilities(device_info)
        
        # Request lossless quality (should fallback to AAC)
        optimal = audio_config_manager.get_optimal_settings(AudioQuality.LOSSLESS)
        assert optimal.codec == AudioCodec.AAC  # Should fallback from LDAC
        
    def test_custom_settings(self, audio_config_manager):
        """Test custom settings."""
        # Set up supported codecs
        device_info = {"supported_codecs": ["sbc", "aac"]}
        audio_config_manager.detect_device_capabilities(device_info)
        
        custom_settings = AudioSettings(
            codec=AudioCodec.AAC,
            quality=AudioQuality.HIGH,
            sample_rate=SampleRate.RATE_48000,
            bit_depth=BitDepth.DEPTH_16,
            bitrate=256000,
            channels=2
        )
        
        success = audio_config_manager.set_custom_settings(custom_settings)
        assert success
        assert audio_config_manager.current_settings.codec == AudioCodec.AAC
        
    def test_setting_update(self, audio_config_manager):
        """Test individual setting updates."""
        # Set up supported codecs
        device_info = {"supported_codecs": ["sbc", "aac"]}
        audio_config_manager.detect_device_capabilities(device_info)
        
        # Update bitrate
        success = audio_config_manager.update_setting("bitrate", 192000)
        assert success
        assert audio_config_manager.current_settings.bitrate == 192000
        
        # Update invalid setting
        success = audio_config_manager.update_setting("invalid_key", "value")
        assert not success
        
    def test_gstreamer_caps(self, audio_config_manager):
        """Test GStreamer capabilities string generation."""
        caps = audio_config_manager.get_gstreamer_caps()
        assert "audio/x-raw" in caps
        assert "rate=44100" in caps
        assert "channels=2" in caps
        
    def test_codec_params(self, audio_config_manager):
        """Test codec parameter generation."""
        # Test SBC parameters
        audio_config_manager.set_quality_preset(AudioQuality.LOW)
        params = audio_config_manager.get_codec_params()
        assert params["codec"] == "sbc"
        assert "allocation" in params
        
        # Test AAC parameters
        device_info = {"supported_codecs": ["aac"]}
        audio_config_manager.detect_device_capabilities(device_info)
        audio_config_manager.set_quality_preset(AudioQuality.HIGH)
        params = audio_config_manager.get_codec_params()
        assert params["codec"] == "aac"
        assert "profile" in params


class TestAudioDiagnostics:
    """Test audio diagnostics."""
    
    @pytest.mark.asyncio
    async def test_system_requirements_check(self, audio_diagnostics):
        """Test system requirements check."""
        with patch("sys.version_info", (3, 9, 0)):
            await audio_diagnostics._check_system_requirements()
            
        results = [r for r in audio_diagnostics._results if r.test_name == "python_version"]
        assert len(results) == 1
        assert results[0].status == "pass"
        
    @pytest.mark.asyncio
    async def test_bluetooth_stack_check(self, audio_diagnostics):
        """Test Bluetooth stack check."""
        with patch("asyncio.create_subprocess_exec") as mock_subprocess:
            # Mock bluetoothctl version check
            mock_process = AsyncMock()
            mock_process.communicate.return_value = (b"bluetoothctl: 5.50\n", b"")
            mock_process.returncode = 0
            mock_subprocess.return_value = mock_process
            
            await audio_diagnostics._check_bluetooth_stack()
            
        results = [r for r in audio_diagnostics._results if r.test_name == "bluetoothctl"]
        assert len(results) == 1
        assert results[0].status == "pass"
        
    @pytest.mark.asyncio
    async def test_audio_stack_check(self, audio_diagnostics):
        """Test audio stack check."""
        # Mock GStreamer availability
        with patch("gi.require_version"), \
             patch("gi.repository.Gst") as mock_gst:
            mock_gst.is_initialized.return_value = True
            mock_gst.version_string.return_value = "GStreamer 1.18.4"
            
            await audio_diagnostics._check_audio_stack()
            
        results = [r for r in audio_diagnostics._results if r.test_name == "gstreamer"]
        assert len(results) == 1
        assert results[0].status == "pass"
        
    @pytest.mark.asyncio
    async def test_bluetooth_devices_check(self, audio_diagnostics):
        """Test Bluetooth devices check."""
        with patch("asyncio.create_subprocess_exec") as mock_subprocess:
            mock_process = AsyncMock()
            mock_process.communicate.return_value = (
                b"Device AA:BB:CC:DD:EE:FF Test Speaker\nDevice 11:22:33:44:55:66 Another Device\n", 
                b""
            )
            mock_process.returncode = 0
            mock_subprocess.return_value = mock_process
            
            await audio_diagnostics._check_bluetooth_devices()
            
        results = [r for r in audio_diagnostics._results if r.test_name == "bluetooth_devices"]
        assert len(results) == 1
        assert results[0].status == "info"
        assert results[0].details["count"] == 2
        
    @pytest.mark.asyncio
    async def test_full_diagnostics(self, audio_diagnostics):
        """Test full diagnostics run."""
        with patch.object(audio_diagnostics, "_check_system_requirements") as mock_sys, \
             patch.object(audio_diagnostics, "_check_bluetooth_stack") as mock_bt, \
             patch.object(audio_diagnostics, "_check_audio_stack") as mock_audio:
            
            result = await audio_diagnostics.run_full_diagnostics()
            
        assert "summary" in result
        assert "results" in result
        assert "total_duration_ms" in result
        assert "recommendations" in result
        
        # Verify all check methods were called
        mock_sys.assert_called_once()
        mock_bt.assert_called_once()
        mock_audio.assert_called_once()
        
    @pytest.mark.asyncio
    async def test_bluetooth_connection_test(self, audio_diagnostics):
        """Test Bluetooth connection test."""
        with patch("asyncio.create_subprocess_exec") as mock_subprocess:
            mock_process = AsyncMock()
            mock_process.communicate.return_value = (b"Connection successful\n", b"")
            mock_process.returncode = 0
            mock_subprocess.return_value = mock_process
            
            result = await audio_diagnostics.test_bluetooth_connection("AA:BB:CC:DD:EE:FF")
            
        assert result["device_address"] == "AA:BB:CC:DD:EE:FF"
        assert result["connection_successful"] is True
        assert "duration_ms" in result
        
    @pytest.mark.asyncio
    async def test_audio_pipeline_test(self, audio_diagnostics):
        """Test audio pipeline test."""
        with patch("asyncio.create_subprocess_exec") as mock_subprocess:
            mock_process = AsyncMock()
            mock_process.communicate.return_value = (b"", b"")
            mock_process.returncode = 0
            mock_subprocess.return_value = mock_process
            
            result = await audio_diagnostics.test_audio_pipeline("sbc")
            
        assert result["codec"] == "sbc"
        assert result["pipeline_successful"] is True
        assert "duration_ms" in result


class TestCoordinatorAudioIntegration:
    """Test coordinator audio integration."""
    
    @pytest.mark.asyncio
    async def test_coordinator_audio_config(self, mock_config_entry):
        """Test coordinator audio configuration integration."""
        with patch("homeassistant.core.HomeAssistant"):
            coordinator = BluetoothAirPlayCoordinator(MagicMock(), mock_config_entry)
            
        # Test audio config property
        assert coordinator.audio_config is not None
        assert isinstance(coordinator.audio_config, AudioConfigManager)
        
    @pytest.mark.asyncio
    async def test_audio_status(self, mock_config_entry):
        """Test audio status retrieval."""
        with patch("homeassistant.core.HomeAssistant"):
            coordinator = BluetoothAirPlayCoordinator(MagicMock(), mock_config_entry)
            
        # Mock audio components
        with patch.object(coordinator._audio_engine, "get_audio_info", return_value={"status": "ready"}), \
             patch.object(coordinator._airplay_server, "get_status", return_value={"running": False}), \
             patch.object(coordinator._mdns_advertiser, "get_status", return_value={"advertising": False}):
            
            status = await coordinator.get_audio_status()
            
        assert "audio_engine" in status
        assert "airplay_server" in status
        assert "mdns_advertiser" in status
        assert "audio_config" in status
        assert "bluetooth_connected" in status
        
    @pytest.mark.asyncio
    async def test_set_audio_quality(self, mock_config_entry):
        """Test setting audio quality."""
        with patch("homeassistant.core.HomeAssistant"):
            coordinator = BluetoothAirPlayCoordinator(MagicMock(), mock_config_entry)
            
        # Mock audio engine methods
        with patch.object(coordinator._audio_engine, "set_codec", return_value=True) as mock_codec, \
             patch.object(coordinator._audio_engine, "set_audio_quality", return_value=True) as mock_quality:
            
            success = await coordinator.set_audio_quality(AudioQuality.HIGH)
            
        assert success
        # Should not call audio engine methods when disconnected
        mock_codec.assert_not_called()
        mock_quality.assert_not_called()
        
    @pytest.mark.asyncio
    async def test_set_audio_quality_connected(self, mock_config_entry):
        """Test setting audio quality when connected."""
        with patch("homeassistant.core.HomeAssistant"):
            coordinator = BluetoothAirPlayCoordinator(MagicMock(), mock_config_entry)
            
        # Set coordinator to connected state
        coordinator._state = "connected"
        
        # Mock audio engine methods
        with patch.object(coordinator._audio_engine, "set_codec", return_value=True) as mock_codec, \
             patch.object(coordinator._audio_engine, "set_audio_quality", return_value=True) as mock_quality:
            
            success = await coordinator.set_audio_quality(AudioQuality.HIGH)
            
        assert success
        # Should call audio engine methods when connected
        mock_codec.assert_called_once()
        mock_quality.assert_called_once()
        
    @pytest.mark.asyncio
    async def test_update_audio_setting(self, mock_config_entry):
        """Test updating individual audio settings."""
        with patch("homeassistant.core.HomeAssistant"):
            coordinator = BluetoothAirPlayCoordinator(MagicMock(), mock_config_entry)
            
        # Set coordinator to connected state
        coordinator._state = "connected"
        
        # Mock audio engine methods
        with patch.object(coordinator._audio_engine, "set_codec", return_value=True) as mock_codec:
            
            success = await coordinator.update_audio_setting("codec", "aac")
            
        assert success
        mock_codec.assert_called_once()


class TestAudioEngineIntegration:
    """Test audio engine integration."""
    
    @pytest.mark.asyncio
    async def test_audio_engine_initialization(self):
        """Test audio engine initialization."""
        from custom_components.bluetooth_to_airplay_bridge.audio_engine import AudioEngine
        
        engine = AudioEngine("AA:BB:CC:DD:EE:FF", "Test AirPlay")
        
        assert engine._bluetooth_address == "AA:BB:CC:DD:EE:FF"
        assert engine._airplay_name == "Test AirPlay"
        assert engine._current_codec == "sbc"
        assert engine._sample_rate == 44100
        
    @pytest.mark.asyncio
    async def test_audio_capture_start_no_gstreamer(self):
        """Test audio capture start without GStreamer."""
        from custom_components.bluetooth_to_airplay_bridge.audio_engine import AudioEngine
        
        with patch("custom_components.bluetooth_to_airplay_bridge.audio_engine.GST_AVAILABLE", False):
            engine = AudioEngine("AA:BB:CC:DD:EE:FF", "Test AirPlay")
            success = await engine.start_audio_capture()
            
        assert not success
        
    @pytest.mark.asyncio
    async def test_codec_setting(self):
        """Test codec setting."""
        from custom_components.bluetooth_to_airplay_bridge.audio_engine import AudioEngine
        
        engine = AudioEngine("AA:BB:CC:DD:EE:FF", "Test AirPlay")
        
        # Test valid codec
        success = await engine.set_codec("aac")
        assert success
        assert engine._current_codec == "aac"
        
        # Test invalid codec
        success = await engine.set_codec("invalid")
        assert not success
        
    @pytest.mark.asyncio
    async def test_audio_quality_setting(self):
        """Test audio quality setting."""
        from custom_components.bluetooth_to_airplay_bridge.audio_engine import AudioEngine
        
        engine = AudioEngine("AA:BB:CC:DD:EE:FF", "Test AirPlay")
        
        success = await engine.set_audio_quality(48000, 2)
        assert success
        assert engine._sample_rate == 48000
        assert engine._channels == 2
        
    def test_audio_info(self):
        """Test audio info retrieval."""
        from custom_components.bluetooth_to_airplay_bridge.audio_engine import AudioEngine
        
        engine = AudioEngine("AA:BB:CC:DD:EE:FF", "Test AirPlay")
        info = engine.get_audio_info()
        
        assert "bluetooth_address" in info
        assert "airplay_name" in info
        assert "current_codec" in info
        assert "sample_rate" in info
        assert "channels" in info
        assert "is_running" in info