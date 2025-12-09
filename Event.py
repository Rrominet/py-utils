"""
Thread-safe event system that executes listener callbacks on the main thread
regardless of which thread emits the event.
"""
import threading
from typing import Callable, Optional, Any
from collections import deque

# Use deque for O(1) append/pop operations instead of list
_main_queue: deque = deque()
_cv = threading.Condition()
_should_stop = threading.Event()


class Event:
    """
    Thread-safe event that can have multiple listeners.
    Listeners are executed on the main event loop thread.
    """
    
    def __init__(self, event_id: str = ""):
        """
        Args:
            event_id: Optional identifier for debugging/filtering
        """
        self.id = event_id
        self._listeners: list[Optional[Callable]] = []
        self._lock = threading.RLock()  # Reentrant lock for nested calls
        self.user_data: Any = None
    
    def add_listener(self, listener: Callable) -> int:
        """
        Register a callback to be invoked when event is emitted.
        
        Args:
            listener: Callable with no required arguments
            
        Returns:
            Index of the listener (use for removal)
            
        Raises:
            TypeError: If listener is not callable
        """
        if not callable(listener):
            raise TypeError(f"Listener must be callable, got {type(listener)}")
        
        with self._lock:
            self._listeners.append(listener)
            return len(self._listeners) - 1
    
    def remove_listener(self, index: int) -> bool:
        """
        Remove a listener by its index.
        
        Args:
            index: The listener index returned by add_listener()
            
        Returns:
            True if removed successfully, False otherwise
        """
        with self._lock:
            if 0 <= index < len(self._listeners):
                self._listeners[index] = None
                return True
            return False
    
    def clear(self) -> None:
        """Remove all listeners from this event."""
        with self._lock:
            self._listeners.clear()
    
    def emit(self) -> None:
        """
        Trigger the event, queuing all active listeners for execution
        on the main thread.
        """
        with self._lock:
            # Clean up None values and get active listeners
            active_listeners = [l for l in self._listeners if l is not None]
            self._listeners = active_listeners  # Update to cleaned list
        
        if active_listeners:
            with _cv:
                _main_queue.extend(active_listeners)
                _cv.notify()
    
    @property
    def listener_count(self) -> int:
        """Get the number of active listeners."""
        with self._lock:
            return sum(1 for l in self._listeners if l is not None)
    
    # Backward compatibility aliases (deprecated)
    def addListener(self, listener: Callable) -> int:
        """Deprecated: Use add_listener() instead"""
        return self.add_listener(listener)
    
    def removeListener(self, index: int) -> bool:
        """Deprecated: Use remove_listener() instead"""
        return self.remove_listener(index)


def run() -> None:
    """
    Main event loop - processes queued listener callbacks.
    This blocks indefinitely and should run on the main thread.
    Call stop() from another thread to exit cleanly.
    """
    while not _should_stop.is_set():
        with _cv:
            # Wait for events or stop signal with timeout
            _cv.wait_for(lambda: len(_main_queue) > 0 or _should_stop.is_set(), 
                        timeout=1.0)
            
            if _should_stop.is_set():
                break
            
            # Process all queued listeners
            while _main_queue:
                listener = _main_queue.popleft()
                try:
                    listener()
                except Exception as e:
                    # Don't let one listener crash the event loop
                    print(f"Error executing listener: {e}")


def run_async() -> threading.Thread:
    """
    Start the event loop in a background daemon thread.
    
    Returns:
        The thread object running the event loop
    """
    thread = threading.Thread(target=run, daemon=True, name="EventLoop")
    thread.start()
    return thread


def stop() -> None:
    """
    Signal the event loop to stop gracefully.
    """
    _should_stop.set()
    with _cv:
        _cv.notify()


# Example usage and testing
if __name__ == "__main__":
    import time
    
    # Example event instance for testing purposes
    ev_test = Event("test_event")
    
    def on_test():
        print(f"Event fired at {time.time():.2f}")
    
    # Add listener using new naming convention
    listener_id = ev_test.add_listener(on_test)
    print(f"Added listener with ID: {listener_id}")
    print(f"Active listeners: {ev_test.listener_count}")
    
    def periodic_test():
        """
        Test function that emits the test event every second
        Used for demonstrating the event system behavior
        """
        for i in range(5):
            time.sleep(1)
            print(f"Emitting event #{i+1}")
            ev_test.emit()
        
        # Stop the event loop after tests
        print("Stopping event loop...")
        stop()
    
    # Start event loop and emitter
    print("Starting event loop in background thread...")
    run_async()
    
    print("Starting periodic emitter...")
    emitter_thread = threading.Thread(target=periodic_test, daemon=True)
    emitter_thread.start()
    
    # Block on main thread
    print("Running main event loop (blocks until stop() is called)...")
    run()
    
    print("Event loop stopped successfully!")
