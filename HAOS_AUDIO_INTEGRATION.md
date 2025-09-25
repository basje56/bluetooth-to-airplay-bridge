# Home Assistant OS Audio Integration

This document describes how the Bluetooth to AirPlay Bridge integration works with Home Assistant OS (HAOS) audio systems.

## Overview

The integration automatically detects and adapts to different Home Assistant environments:

- **HAOS (Home Assistant OS)**: Uses the `hassio_audio` container
- **Supervised**: Uses Home Assistant CLI and container methods
- **Container**: Uses direct pactl or HA CLI
- **Standalone**: Uses direct pactl installation

## HAOS Audio Architecture

In Home Assistant OS, audio is managed through a dedicated `hassio_audio` container that runs PulseAudio. This container:

- Handles ALSA settings and PulseAudio service
- Exposes PulseAudio to Home Assistant and add-ons
- Provides centralized audio configuration management
- Allows full user control over audio modules

## Detection Methods

The integration uses multiple detection methods in order of preference:

### 1. Environment Detection

First, the integration detects the Home Assistant environment:

```python
# Check for HAOS by looking for hassio_audio container
docker ps --filter name=hassio_audio

# Check for Home Assistant CLI
ha --version

# Check if running inside HA container
/proc/1/cgroup content analysis
```

### 2. PulseAudio Access Methods

Based on the detected environment, different methods are tried:

#### HAOS Environment
1. **Container Method**: `docker exec -i hassio_audio pactl <command>`
2. **HA CLI Method**: `ha audio <command>`

#### Supervised Environment
1. **HA CLI Method**: `ha audio <command>`
2. **Container Method**: `docker exec -i hassio_audio pactl <command>`
3. **Direct Method**: `pactl <command>`

#### Container Environment
1. **Direct Method**: `pactl <command>`
2. **HA CLI Method**: `ha audio <command>`

#### Standalone Environment
1. **Direct Method**: `pactl <command>`
2. **Container Method**: `docker exec -i hassio_audio pactl <command>` (fallback)
3. **HA CLI Method**: `ha audio <command>` (fallback)

## Command Mapping

### PulseAudio Commands → HAOS Methods

| PulseAudio Command | HAOS Container | HA CLI Alternative |
|-------------------|----------------|-------------------|
| `pactl --version` | `docker exec -i hassio_audio pactl --version` | `ha audio info` |
| `pactl list sources` | `docker exec -i hassio_audio pactl list sources` | `ha audio info` |
| `pactl list sources short` | `docker exec -i hassio_audio pactl list sources short` | `ha audio info` |
| `pactl set-source-volume` | `docker exec -i hassio_audio pactl set-source-volume` | `ha audio volume --source <name> --volume <vol>` |
| `pactl list sinks` | `docker exec -i hassio_audio pactl list sinks` | `ha audio info` |

### Home Assistant CLI Commands

Available HA CLI audio commands:

- `ha audio default` - Set default input/output audio device
- `ha audio info` - Provides information about HA Audio devices
- `ha audio logs` - View the log output of HA Audio
- `ha audio profile` - Set the HA Audio profile for a card
- `ha audio reload` - Reload HA Audio updating information
- `ha audio restart` - Restarts the internal HA Audio container
- `ha audio stats` - Provides system usage stats of HA Audio
- `ha audio update` - Update the HA Audio container
- `ha audio volume` - Audio device volume control

## Bluetooth Audio Detection

The integration detects Bluetooth audio sources using standard BlueZ naming:

```
bluez_source.{MAC_ADDRESS}.a2dp_source
```

Where `{MAC_ADDRESS}` is the Bluetooth device MAC address with colons replaced by underscores.

## Error Handling

The integration includes comprehensive error handling:

1. **Method Fallback**: If one method fails, it tries alternative methods
2. **Environment Adaptation**: Automatically adapts to different HA environments
3. **Graceful Degradation**: Continues operation with reduced functionality if needed
4. **Detailed Logging**: Provides debug information for troubleshooting

## Troubleshooting

### Common Issues

1. **PulseAudio Not Detected**
   - Check if `hassio_audio` container is running: `docker ps | grep hassio_audio`
   - Verify HA CLI is available: `ha audio info`
   - Check integration logs for detection attempts

2. **Volume Control Not Working**
   - Ensure Bluetooth device is connected and active
   - Check PulseAudio source availability: `docker exec -i hassio_audio pactl list sources`
   - Verify source naming matches BlueZ convention

3. **Container Access Issues**
   - Ensure Docker is available and accessible
   - Check container permissions
   - Verify `hassio_audio` container is healthy

### Debug Commands

For troubleshooting, you can manually test commands:

```bash
# Test container access
docker exec -i hassio_audio pactl --version

# List audio sources
docker exec -i hassio_audio pactl list sources short

# Test HA CLI
ha audio info

# Check container status
docker ps --filter name=hassio_audio
```

## Requirements

### HAOS Environment
- Home Assistant OS with audio container enabled
- Docker access (usually available by default)
- Bluetooth device paired and connected

### Supervised Environment
- Home Assistant Supervised installation
- Home Assistant CLI available
- PulseAudio or audio container access

### Container Environment
- Home Assistant Container installation
- PulseAudio installed on host system
- Proper audio device permissions

### Standalone Environment
- Home Assistant Core installation
- PulseAudio installed and configured
- Bluetooth support enabled

## Security Considerations

- Container access is read-only where possible
- No persistent changes to audio configuration
- Temporary volume adjustments only
- Respects existing PulseAudio security settings

## Performance

- Minimal overhead with smart environment detection
- Cached detection results to avoid repeated checks
- Efficient command execution with proper error handling
- Asynchronous operations to prevent blocking