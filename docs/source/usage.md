## Usage

### Listing devices

```python
devinput.list_devices()
#  -> [<Device 'Logitech Wireless Receiver Mouse' (/dev/input/event16)>, ... 
```

### Listing all devices with a given set of capabilities

```python
devinput.list_capable_devices(devinput.KeyEvent.KEY_A)

# -> [<Device 'AT Translated Set 2 keyboard' (/dev/input/event3)>]
```

### Creating a device

```python
dev = devinput.Device("/dev/input/event6")
# =
dev = devinput.Device.from_event("event6")
```

### Querying device capabilities
Call `dev.open()` first (or do this inside the `with` block).
```python
dev.has_cap(devinput.EventType.EV_ABS)
dev.has_cap(devinput.AbsEvent.ABS_X)
```
#### List all capabilities of a given type

```
dev.capabilities.list(devinput.EventType.EV_ABS)
```

#### Get all event types supported by the device

```
dev.capabilities.event_types
```

### Reading events

```python
# ...
with dev:
    event = dev.get_event()
```

### Polling

```python
with dev:
    dev.poll()
```

Returns whether an event is available immediately or within a given timeout.

```python
with dev:
    dev.wait()
```
Waits until an event is available.

### Sending events

```python
with dev:
    dev.dev.send_event(devinput.Event(devinput.KeyEvent.KEY_A,1))
```

### Grabbing

```python
with (dev, dev.grabbed()):
    # ...
```

### Async

#### Reading events

```python
with dev:
    await dev.get_event_async()
```

#### Polling

```python
with dev:
    await dev.poll_async()
    await dev.wait()
```

#### Sending events

```python
with dev:
    await dev.send_event_async(devinput.Event(...))
```

## Examples

Check out the [examples](https://github.com/jenca-adam/devinput/tree/main/examples) on GitHub for more complex usage.


