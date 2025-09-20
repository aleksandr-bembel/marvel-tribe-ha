"""WebSocket client for Marvel Tribe communication."""

from __future__ import annotations

import asyncio
import json
import logging
from typing import Any, Callable, Dict, Optional

import websockets
from websockets.exceptions import ConnectionClosed, WebSocketException

from .const import WS_ENDPOINT

_LOGGER = logging.getLogger(__name__)


class MarvelTribeWebSocketClient:
    """WebSocket client for Marvel Tribe communication."""

    def __init__(self, host: str, port: int = 80):
        """Initialize the WebSocket client."""
        self.host = host
        self.port = port
        self.websocket: Optional[websockets.WebSocketServerProtocol] = None
        self.connected = False
        self.message_handlers: Dict[str, Callable] = {}
        self._reconnect_task: Optional[asyncio.Task] = None
        
        # Protocol based on reverse engineering results
        self.command_id = {
            "log": 0,
            "set_user_property": 1,
            "get_user_property": 2,
            "recovery": 3,
            "file": 4,
            "factory": 5,
            "wifi": 6,
            "ble": 7,
            "characteristic": 8,
            "audio": 9,
        }
        
        self.command_wifi_id = {
            "scan_ap": 0,
            "scan_status": 1,
            "ap_list": 2,
            "wifi_status": 3,
            "connect": 4,
        }
        
        self.property_id = {
            "operate": 0,
            "all": 1,
            "authorization": 2,
            "time": 3,
            "alarm": 4,
            "sntp": 5,
            "auto_sleep": 6,
            "rgb_light": 7,
            "wifi": 8,
            "audio": 9,
            "album": 10,
            "weather": 11,
            "others": 12,
            "fans": 13,
            "dst": 14,
            "max": 15,
        }

    @property
    def ws_url(self) -> str:
        """Get WebSocket URL."""
        return f"ws://{self.host}:{self.port}{WS_ENDPOINT}"

    async def test_connection(self) -> bool:
        """Test WebSocket connection."""
        try:
            async with websockets.connect(
                self.ws_url, 
                ping_interval=None,  # Disable ping for testing
                close_timeout=5
            ) as websocket:
                # Send a test message to verify connection
                test_message = {"type": "ping", "data": {}}
                await websocket.send(json.dumps(test_message))
                
                # Try to receive a response
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                    _LOGGER.info("Test connection successful. Response: %s", response)
                    return True
                except asyncio.TimeoutError:
                    _LOGGER.warning("No response to test message, but connection established")
                    return True
                    
        except Exception as err:
            _LOGGER.error("Test connection failed: %s", err)
            raise

    async def connect(self) -> bool:
        """Connect to WebSocket."""
        # Clean up any existing connection
        await self.disconnect()
        
        try:
            _LOGGER.info("Connecting to Marvel Tribe at %s", self.ws_url)
            self.websocket = await websockets.connect(
                self.ws_url,
                ping_interval=30,
                ping_timeout=10,
                close_timeout=5
            )
            self.connected = True
            _LOGGER.info("Successfully connected to Marvel Tribe")
            
            # Start listening for messages
            self._reconnect_task = asyncio.create_task(self._listen())
            
            return True
        except Exception as err:
            _LOGGER.error("Failed to connect to Marvel Tribe: %s", err)
            self.connected = False
            self.websocket = None
            return False

    async def disconnect(self):
        """Disconnect from WebSocket."""
        _LOGGER.debug("Disconnecting from WebSocket...")
        self.connected = False
        
        # Cancel listen task
        if self._reconnect_task and not self._reconnect_task.cancelled():
            self._reconnect_task.cancel()
            try:
                await self._reconnect_task
            except asyncio.CancelledError:
                pass
            self._reconnect_task = None
            
        # Close websocket
        if self.websocket:
            try:
                await self.websocket.close()
            except Exception as err:
                _LOGGER.debug("Error closing websocket: %s", err)
            self.websocket = None
        
        _LOGGER.debug("WebSocket disconnected")

    async def _listen(self):
        """Listen for incoming messages."""
        while self.connected and self.websocket:
            try:
                message = await self.websocket.recv()
                await self._handle_message(message)
            except ConnectionClosed:
                _LOGGER.info("WebSocket connection closed normally")
                await self._handle_disconnect()
                break
            except WebSocketException as err:
                _LOGGER.warning("WebSocket error: %s", err)
                await self._handle_disconnect()
                break
            except Exception as err:
                _LOGGER.error("Unexpected error in _listen: %s", err)
                await self._handle_disconnect()
                break

    async def _handle_message(self, message: str):
        """Handle incoming message."""
        try:
            data = json.loads(message)
            _LOGGER.debug("Received message: %s", data)
            
            # Handle Marvel Tribe protocol messages
            if "command" in data:
                # Send to Marvel Tribe response handler
                if "marvel_tribe_data" in self.message_handlers:
                    await self.message_handlers["marvel_tribe_data"](data)
                
                # Also handle specific protocol messages
                command = data["command"]
                await self._handle_protocol_message(command, data)
            else:
                # Fallback to old message handling
                message_type = data.get("type", "unknown")
                if message_type in self.message_handlers:
                    await self.message_handlers[message_type](data)
                else:
                    _LOGGER.debug("Unhandled message type: %s", message_type)
                
        except json.JSONDecodeError:
            _LOGGER.warning("Received non-JSON message: %s", message)
        except Exception as err:
            _LOGGER.error("Error handling message: %s", err)

    async def _handle_protocol_message(self, command: int, data: dict):
        """Handle Marvel Tribe protocol message."""
        try:
            # All protocol messages are handled by coordinator's marvel_tribe_data handler
            _LOGGER.debug("Protocol command %s: %s", command, data)
        except Exception as err:
            _LOGGER.error("Error handling protocol message: %s", err)

    async def _handle_disconnect(self):
        """Handle disconnection."""
        _LOGGER.info("Handling disconnection...")
        self.connected = False
        
        # Cancel the listen task if it exists
        if self._reconnect_task and not self._reconnect_task.cancelled():
            self._reconnect_task.cancel()
            self._reconnect_task = None
        
        # Close websocket connection
        if self.websocket:
            try:
                await self.websocket.close()
            except Exception:
                pass  # Ignore errors when closing
            self.websocket = None
        
        # Don't automatically reconnect here - let coordinator handle it
        _LOGGER.info("WebSocket disconnected. Coordinator will handle reconnection.")

    async def send_message(self, message_type: str, data: Dict[str, Any] = None) -> bool:
        """Send a message to the device."""
        if not self.connected or not self.websocket:
            _LOGGER.error("Not connected to device")
            return False

        try:
            message = {
                "type": message_type,
                "data": data or {}
            }
            await self.websocket.send(json.dumps(message))
            _LOGGER.debug("Sent message: %s", message)
            return True
        except Exception as err:
            _LOGGER.error("Failed to send message: %s", err)
            return False

    def register_message_handler(self, message_type: str, handler: Callable):
        """Register a handler for a specific message type."""
        self.message_handlers[message_type] = handler

    async def send_protocol_command(self, command_type: str, **kwargs) -> bool:
        """Send a protocol command to the device."""
        if not self.connected or not self.websocket:
            _LOGGER.error("Not connected to device")
            return False

        try:
            message = {"command": self.command_id[command_type]}
            message.update(kwargs)
            
            await self.websocket.send(json.dumps(message))
            _LOGGER.debug("Sent protocol command %s: %s", command_type, message)
            return True
        except Exception as err:
            _LOGGER.error("Failed to send protocol command: %s", err)
            return False

    async def send_wifi_command(self, wifi_command: str, **kwargs) -> bool:
        """Send a WiFi command."""
        if not self.connected or not self.websocket:
            _LOGGER.error("Not connected to device")
            return False

        try:
            message = {"command": self.command_id["wifi"]}
            message[self.command_wifi_id[wifi_command]] = kwargs.get("data", 0)
            
            await self.websocket.send(json.dumps(message))
            _LOGGER.debug("Sent WiFi command %s: %s", wifi_command, message)
            return True
        except Exception as err:
            _LOGGER.error("Failed to send WiFi command: %s", err)
            return False

    async def send_property_command(self, command_type: str, property_name: str, data=None) -> bool:
        """Send a property command (get/set)."""
        if not self.connected or not self.websocket:
            _LOGGER.error("Not connected to device")
            return False

        try:
            message = {"command": self.command_id[command_type]}
            
            # For set commands, send the entire data object (not JSON string!)
            if command_type == "set_user_property" and data:
                message[self.property_id[property_name]] = data
            else:
                message[self.property_id[property_name]] = data if data is not None else "0"
            
            await self.websocket.send(json.dumps(message))
            _LOGGER.debug("Sent property command %s/%s: %s", command_type, property_name, message)
            return True
        except Exception as err:
            _LOGGER.error("Failed to send property command: %s", err)
            return False

    async def get_all_properties(self) -> bool:
        """Get all device properties."""
        return await self.send_property_command("get_user_property", "all")

    async def get_status(self) -> bool:
        """Request device status."""
        return await self.get_all_properties()

    async def get_battery(self) -> bool:
        """Request battery level."""
        return await self.send_property_command("get_user_property", "operate")

    async def get_time(self) -> bool:
        """Request current time."""
        return await self.send_property_command("get_user_property", "time")

