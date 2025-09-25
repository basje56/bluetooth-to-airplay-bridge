"""Audio configuration and quality settings for Bluetooth to AirPlay Bridge."""
from __future__ import annotations

import logging
from dataclasses import dataclass, replace
from enum import Enum
from typing import Any, Optional

_LOGGER = logging.getLogger(__name__)


class AudioCodec(Enum):
    """Supported audio codecs."""
    SBC = "sbc"
    AAC = "aac"
    APTX = "aptx"
    APTX_HD = "aptx_hd"
    LDAC = "ldac"


class AudioQuality(Enum):
    """Audio quality presets."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    LOSSLESS = "lossless"


class SampleRate(Enum):
    """Supported sample rates."""
    RATE_44100 = 44100
    RATE_48000 = 48000
    RATE_88200 = 88200
    RATE_96000 = 96000
    RATE_176400 = 176400
    RATE_192000 = 192000


class BitDepth(Enum):
    """Supported bit depths."""
    DEPTH_16 = 16
    DEPTH_24 = 24
    DEPTH_32 = 32


@dataclass
class AudioSettings:
    """Audio configuration settings."""
    codec: AudioCodec = AudioCodec.SBC
    quality: AudioQuality = AudioQuality.MEDIUM
    sample_rate: SampleRate = SampleRate.RATE_44100
    bit_depth: BitDepth = BitDepth.DEPTH_16
    bitrate: Optional[int] = None
    channels: int = 2
    buffer_size: int = 1024
    latency_ms: int = 100
    enable_noise_reduction: bool = False
    enable_echo_cancellation: bool = False
    volume_normalization: bool = True
    dynamic_range_compression: bool = False


class AudioConfigManager:
    """Manages audio configuration and quality settings."""
    
    # Quality presets mapping
    QUALITY_PRESETS = {
        AudioQuality.LOW: AudioSettings(
            codec=AudioCodec.SBC,
            quality=AudioQuality.LOW,
            sample_rate=SampleRate.RATE_44100,
            bit_depth=BitDepth.DEPTH_16,
            bitrate=128000,
            buffer_size=2048,
            latency_ms=150,
            enable_noise_reduction=True,
            volume_normalization=True
        ),
        AudioQuality.MEDIUM: AudioSettings(
            codec=AudioCodec.SBC,
            quality=AudioQuality.MEDIUM,
            sample_rate=SampleRate.RATE_44100,
            bit_depth=BitDepth.DEPTH_16,
            bitrate=256000,
            buffer_size=1024,
            latency_ms=100,
            enable_noise_reduction=False,
            volume_normalization=True
        ),
        AudioQuality.HIGH: AudioSettings(
            codec=AudioCodec.AAC,
            quality=AudioQuality.HIGH,
            sample_rate=SampleRate.RATE_48000,
            bit_depth=BitDepth.DEPTH_24,
            bitrate=320000,
            buffer_size=512,
            latency_ms=80,
            enable_noise_reduction=False,
            volume_normalization=True,
            dynamic_range_compression=False
        ),
        AudioQuality.LOSSLESS: AudioSettings(
            codec=AudioCodec.LDAC,
            quality=AudioQuality.LOSSLESS,
            sample_rate=SampleRate.RATE_96000,
            bit_depth=BitDepth.DEPTH_24,
            bitrate=990000,
            buffer_size=256,
            latency_ms=60,
            enable_noise_reduction=False,
            volume_normalization=False,
            dynamic_range_compression=False
        )
    }
    
    # Codec capabilities
    CODEC_CAPABILITIES = {
        AudioCodec.SBC: {
            "max_sample_rate": SampleRate.RATE_48000,
            "max_bit_depth": BitDepth.DEPTH_16,
            "max_bitrate": 328000,
            "supported_channels": [1, 2],
            "latency_range": (80, 200)
        },
        AudioCodec.AAC: {
            "max_sample_rate": SampleRate.RATE_48000,
            "max_bit_depth": BitDepth.DEPTH_24,
            "max_bitrate": 320000,
            "supported_channels": [1, 2],
            "latency_range": (60, 150)
        },
        AudioCodec.APTX: {
            "max_sample_rate": SampleRate.RATE_48000,
            "max_bit_depth": BitDepth.DEPTH_16,
            "max_bitrate": 352000,
            "supported_channels": [1, 2],
            "latency_range": (40, 100)
        },
        AudioCodec.APTX_HD: {
            "max_sample_rate": SampleRate.RATE_48000,
            "max_bit_depth": BitDepth.DEPTH_24,
            "max_bitrate": 576000,
            "supported_channels": [1, 2],
            "latency_range": (40, 100)
        },
        AudioCodec.LDAC: {
            "max_sample_rate": SampleRate.RATE_96000,
            "max_bit_depth": BitDepth.DEPTH_24,
            "max_bitrate": 990000,
            "supported_channels": [1, 2],
            "latency_range": (20, 80)
        }
    }
    
    def __init__(self) -> None:
        """Initialize audio configuration manager."""
        self._current_settings = replace(self.QUALITY_PRESETS[AudioQuality.MEDIUM])
        self._supported_codecs: list[AudioCodec] = []
        self._device_capabilities: dict[str, Any] = {}
        
    @property
    def current_settings(self) -> AudioSettings:
        """Get current audio settings."""
        return self._current_settings
        
    @property
    def supported_codecs(self) -> list[AudioCodec]:
        """Get list of supported codecs."""
        return self._supported_codecs.copy()
        
    def set_quality_preset(self, quality: AudioQuality) -> bool:
        """Set audio quality preset."""
        if quality not in self.QUALITY_PRESETS:
            _LOGGER.error("Unsupported quality preset: %s", quality)
            return False
            
        preset = self.QUALITY_PRESETS[quality]
        
        # Validate codec support
        if preset.codec not in self._supported_codecs:
            _LOGGER.warning("Codec %s not supported, falling back to SBC", preset.codec)
            preset.codec = AudioCodec.SBC
            
        self._current_settings = replace(preset)
        _LOGGER.info("Audio quality set to %s", quality.value)
        return True
        
    def set_custom_settings(self, settings: AudioSettings) -> bool:
        """Set custom audio settings."""
        if not self._validate_settings(settings):
            return False
            
        self._current_settings = settings
        _LOGGER.info("Custom audio settings applied")
        return True
        
    def update_setting(self, key: str, value: Any) -> bool:
        """Update a specific audio setting."""
        if not hasattr(self._current_settings, key):
            _LOGGER.error("Invalid setting key: %s", key)
            return False
            
        # Create a copy and update
        new_settings = self._current_settings.__class__(**self._current_settings.__dict__)
        setattr(new_settings, key, value)
        
        if not self._validate_settings(new_settings):
            return False
            
        setattr(self._current_settings, key, value)
        _LOGGER.debug("Updated audio setting %s to %s", key, value)
        return True
        
    def detect_device_capabilities(self, device_info: dict[str, Any]) -> None:
        """Detect and store device audio capabilities."""
        self._device_capabilities = device_info
        
        # Extract supported codecs from device info
        supported_codecs = device_info.get("supported_codecs", [])
        self._supported_codecs = []
        
        for codec_name in supported_codecs:
            try:
                codec = AudioCodec(codec_name.lower())
                self._supported_codecs.append(codec)
            except ValueError:
                _LOGGER.debug("Unknown codec: %s", codec_name)
                
        # Fallback to SBC if no codecs detected
        if not self._supported_codecs:
            self._supported_codecs = [AudioCodec.SBC]
            
        _LOGGER.info("Detected supported codecs: %s", 
                    [codec.value for codec in self._supported_codecs])
        
    def get_optimal_settings(self, target_quality: AudioQuality) -> AudioSettings:
        """Get optimal settings for target quality based on device capabilities."""
        base_settings = self.QUALITY_PRESETS[target_quality]
        
        # Check if target codec is supported
        if base_settings.codec not in self._supported_codecs:
            # Find best alternative codec
            codec_priority = [AudioCodec.LDAC, AudioCodec.APTX_HD, AudioCodec.APTX, 
                            AudioCodec.AAC, AudioCodec.SBC]
            
            for codec in codec_priority:
                if codec in self._supported_codecs:
                    base_settings.codec = codec
                    break
                    
        # Adjust settings based on codec capabilities
        capabilities = self.CODEC_CAPABILITIES.get(base_settings.codec, {})
        
        # Limit sample rate
        max_sample_rate = capabilities.get("max_sample_rate")
        if max_sample_rate and base_settings.sample_rate.value > max_sample_rate.value:
            base_settings.sample_rate = max_sample_rate
            
        # Limit bit depth
        max_bit_depth = capabilities.get("max_bit_depth")
        if max_bit_depth and base_settings.bit_depth.value > max_bit_depth.value:
            base_settings.bit_depth = max_bit_depth
            
        # Limit bitrate
        max_bitrate = capabilities.get("max_bitrate")
        if max_bitrate and base_settings.bitrate and base_settings.bitrate > max_bitrate:
            base_settings.bitrate = max_bitrate
            
        return base_settings
        
    def _validate_settings(self, settings: AudioSettings) -> bool:
        """Validate audio settings."""
        # Check codec support
        if settings.codec not in self._supported_codecs:
            _LOGGER.error("Codec %s not supported", settings.codec)
            return False
            
        # Check codec capabilities
        capabilities = self.CODEC_CAPABILITIES.get(settings.codec)
        if not capabilities:
            _LOGGER.error("No capabilities defined for codec %s", settings.codec)
            return False
            
        # Validate sample rate
        max_sample_rate = capabilities["max_sample_rate"]
        if settings.sample_rate.value > max_sample_rate.value:
            _LOGGER.error("Sample rate %d exceeds maximum %d for codec %s",
                         settings.sample_rate.value, max_sample_rate.value, settings.codec)
            return False
            
        # Validate bit depth
        max_bit_depth = capabilities["max_bit_depth"]
        if settings.bit_depth.value > max_bit_depth.value:
            _LOGGER.error("Bit depth %d exceeds maximum %d for codec %s",
                         settings.bit_depth.value, max_bit_depth.value, settings.codec)
            return False
            
        # Validate bitrate
        max_bitrate = capabilities["max_bitrate"]
        if settings.bitrate and settings.bitrate > max_bitrate:
            _LOGGER.error("Bitrate %d exceeds maximum %d for codec %s",
                         settings.bitrate, max_bitrate, settings.codec)
            return False
            
        # Validate channels
        supported_channels = capabilities["supported_channels"]
        if settings.channels not in supported_channels:
            _LOGGER.error("Channel count %d not supported for codec %s",
                         settings.channels, settings.codec)
            return False
            
        return True
        
    def get_settings_dict(self) -> dict[str, Any]:
        """Get current settings as dictionary."""
        return {
            "codec": self._current_settings.codec.value,
            "quality": self._current_settings.quality.value,
            "sample_rate": self._current_settings.sample_rate.value,
            "bit_depth": self._current_settings.bit_depth.value,
            "bitrate": self._current_settings.bitrate,
            "channels": self._current_settings.channels,
            "buffer_size": self._current_settings.buffer_size,
            "latency_ms": self._current_settings.latency_ms,
            "enable_noise_reduction": self._current_settings.enable_noise_reduction,
            "enable_echo_cancellation": self._current_settings.enable_echo_cancellation,
            "volume_normalization": self._current_settings.volume_normalization,
            "dynamic_range_compression": self._current_settings.dynamic_range_compression
        }
        
    def get_gstreamer_caps(self) -> str:
        """Get GStreamer capabilities string for current settings."""
        settings = self._current_settings
        
        caps = f"audio/x-raw,format=S{settings.bit_depth.value}LE," \
               f"rate={settings.sample_rate.value}," \
               f"channels={settings.channels}"
               
        return caps
        
    def get_pulseaudio_format(self) -> str:
        """Get PulseAudio format string for current settings."""
        settings = self._current_settings
        
        # Convert bit depth to PulseAudio format
        if settings.bit_depth.value == 16:
            format_str = "s16le"
        elif settings.bit_depth.value == 24:
            format_str = "s24le"
        elif settings.bit_depth.value == 32:
            format_str = "s32le"
        else:
            format_str = "s16le"  # Default fallback
            
        return f"{format_str},{settings.sample_rate.value},{settings.channels}"
        
    def get_codec_params(self) -> dict[str, Any]:
        """Get codec-specific parameters for current settings."""
        settings = self._current_settings
        
        params = {
            "codec": settings.codec.value,
            "bitrate": settings.bitrate,
            "sample_rate": settings.sample_rate.value,
            "channels": settings.channels
        }
        
        # Add codec-specific parameters
        if settings.codec == AudioCodec.SBC:
            params.update({
                "allocation": "loudness",
                "subbands": 8,
                "blocks": 16
            })
        elif settings.codec == AudioCodec.AAC:
            params.update({
                "profile": "lc",
                "vbr": True
            })
        elif settings.codec in [AudioCodec.APTX, AudioCodec.APTX_HD]:
            params.update({
                "variant": "hd" if settings.codec == AudioCodec.APTX_HD else "classic"
            })
        elif settings.codec == AudioCodec.LDAC:
            params.update({
                "eqmid": 0,  # High quality mode
                "channel_mode": "stereo"
            })
            
        return params


# Global audio configuration manager instance
audio_config = AudioConfigManager()