#!/usr/bin/env python3
"""
OxenORM Signals System

This module provides the signals functionality for OxenORM,
which allows for hooks into model lifecycle events.
"""

from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Type, TYPE_CHECKING

if TYPE_CHECKING:
    from oxen.models import Model


class Signals(Enum):
    """Signal types for model lifecycle events."""
    pre_save = "pre_save"
    post_save = "post_save"
    pre_delete = "pre_delete"
    post_delete = "post_delete"


class SignalManager:
    """
    Manager for handling signals.
    
    This class manages the registration and dispatching of signals.
    """

    def __init__(self):
        """Initialize the signal manager."""
        self._receivers: Dict[Signals, Dict[Type["Model"], List[Callable]]] = {
            signal: {} for signal in Signals
        }

    def connect(self, signal: Signals, sender: Type["Model"], receiver: Callable) -> None:
        """
        Connect a receiver to a signal.
        
        Args:
            signal: The signal to connect to
            sender: The model class that sends the signal
            receiver: The function to call when the signal is sent
        """
        if signal not in self._receivers:
            self._receivers[signal] = {}
        
        if sender not in self._receivers[signal]:
            self._receivers[signal][sender] = []
        
        self._receivers[signal][sender].append(receiver)

    def disconnect(self, signal: Signals, sender: Type["Model"], receiver: Callable) -> None:
        """
        Disconnect a receiver from a signal.
        
        Args:
            signal: The signal to disconnect from
            sender: The model class that sends the signal
            receiver: The function to disconnect
        """
        if signal in self._receivers and sender in self._receivers[signal]:
            if receiver in self._receivers[signal][sender]:
                self._receivers[signal][sender].remove(receiver)

    async def send(self, signal: Signals, sender: Type["Model"], **kwargs: Any) -> List[tuple[Callable, Any]]:
        """
        Send a signal to all connected receivers.
        
        Args:
            signal: The signal to send
            sender: The model class sending the signal
            **kwargs: Additional arguments to pass to receivers
            
        Returns:
            List of (receiver, response) tuples
        """
        responses = []
        
        if signal in self._receivers and sender in self._receivers[signal]:
            for receiver in self._receivers[signal][sender]:
                try:
                    if hasattr(receiver, '__await__'):
                        response = await receiver(sender, **kwargs)
                    else:
                        response = receiver(sender, **kwargs)
                    responses.append((receiver, response))
                except Exception as e:
                    # Log the error but don't stop other receivers
                    print(f"Error in signal receiver {receiver}: {e}")
                    responses.append((receiver, None))
        
        return responses

    def get_receivers(self, signal: Signals, sender: Type["Model"]) -> List[Callable]:
        """
        Get all receivers for a signal and sender.
        
        Args:
            signal: The signal
            sender: The model class
            
        Returns:
            List of receiver functions
        """
        if signal in self._receivers and sender in self._receivers[signal]:
            return self._receivers[signal][sender].copy()
        return []

    def clear(self, signal: Optional[Signals] = None, sender: Optional[Type["Model"]] = None) -> None:
        """
        Clear signal receivers.
        
        Args:
            signal: The signal to clear (None for all signals)
            sender: The model class to clear (None for all senders)
        """
        if signal is None:
            # Clear all signals
            self._receivers = {signal: {} for signal in Signals}
        elif sender is None:
            # Clear all senders for a specific signal
            if signal in self._receivers:
                self._receivers[signal] = {}
        else:
            # Clear specific signal and sender
            if signal in self._receivers and sender in self._receivers[signal]:
                self._receivers[signal][sender] = []


# Global signal manager instance
signal_manager = SignalManager()


def connect(signal: Signals, sender: Type["Model"], receiver: Callable) -> None:
    """
    Connect a receiver to a signal.
    
    Args:
        signal: The signal to connect to
        sender: The model class that sends the signal
        receiver: The function to call when the signal is sent
    """
    signal_manager.connect(signal, sender, receiver)


def disconnect(signal: Signals, sender: Type["Model"], receiver: Callable) -> None:
    """
    Disconnect a receiver from a signal.
    
    Args:
        signal: The signal to disconnect from
        sender: The model class that sends the signal
        receiver: The function to disconnect
    """
    signal_manager.disconnect(signal, sender, receiver)


async def send(signal: Signals, sender: Type["Model"], **kwargs: Any) -> List[tuple[Callable, Any]]:
    """
    Send a signal to all connected receivers.
    
    Args:
        signal: The signal to send
        sender: The model class sending the signal
        **kwargs: Additional arguments to pass to receivers
        
    Returns:
        List of (receiver, response) tuples
    """
    return await signal_manager.send(signal, sender, **kwargs)


def receiver(signal: Signals, sender: Type["Model"]):
    """
    Decorator to register a function as a signal receiver.
    
    Args:
        signal: The signal to connect to
        sender: The model class that sends the signal
        
    Returns:
        Decorator function
    """
    def decorator(func: Callable) -> Callable:
        connect(signal, sender, func)
        return func
    return decorator


# Convenience decorators for common signals
def pre_save(sender: Type["Model"]):
    """Decorator for pre_save signal."""
    return receiver(Signals.pre_save, sender)


def post_save(sender: Type["Model"]):
    """Decorator for post_save signal."""
    return receiver(Signals.post_save, sender)


def pre_delete(sender: Type["Model"]):
    """Decorator for pre_delete signal."""
    return receiver(Signals.pre_delete, sender)


def post_delete(sender: Type["Model"]):
    """Decorator for post_delete signal."""
    return receiver(Signals.post_delete, sender)


# Example usage:
# @pre_save(User)
# async def user_pre_save(sender, instance, **kwargs):
#     print(f"About to save user: {instance}")
#
# @post_save(User)
# async def user_post_save(sender, instance, created, **kwargs):
#     if created:
#         print(f"Created new user: {instance}")
#     else:
#         print(f"Updated user: {instance}") 