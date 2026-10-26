# Line 1:  Import json for serializing memory snapshots (useful for debugging).
import json

# Line 2:  Import time to timestamp memory entries so you can see when things were stored.
import time


# Line 5:  Define the Memory class — a simple in-memory key-value store with timestamps.
class Memory:
    # Line 7:  Constructor initializes an empty dict and a list to preserve insertion order.
    def __init__(self):
        # Line 8:  Store entries as {key: (value, timestamp)} for quick lookup by key.
        self._store = {}
        # Line 9:  Keep a list of keys in insertion order so memory_list is deterministic.
        self._order = []

    # Line 12:  Store a value under a key, overwriting if the key already exists.
    def store(self, key, value):
        # Line 13:  If key is new, append to order list to track first-insertion position.
        if key not in self._store:
            # Line 14:  Record the key in our ordered list for stable listing.
            self._order.append(key)
        # Line 15:  Store the value with a timestamp so we know when it was written.
        self._store[key] = (value, time.time())

    # Line 18:  Retrieve a value by key; returns None if the key was never stored.
    def recall(self, key):
        # Line 19:  Look up the key in our dict; use .get() to avoid KeyError on missing keys.
        entry = self._store.get(key)
        # Line 20:  If entry exists, return just the value (discard the timestamp).
        if entry is not None:
            # Line 21:  Return the first element of the tuple which is the stored value.
            return entry[0]
        # Line 23:  Key was never stored, so return None to signal "not found" to caller.
        return None

    # Line 26:  Return all keys in insertion order (useful for memory_list tool).
    def list_keys(self):
        # Line 27:  Return a copy of the order list so external code can't mutate internals.
        return list(self._order)

    # Line 30:  Remove a key from memory; returns True if it existed, False otherwise.
    def delete(self, key):
        # Line 31:  Check if the key exists before attempting removal to give accurate result.
        if key in self._store:
            # Line 32:  Remove from the dict store.
            del self._store[key]
            # Line 33:  Also remove from the order list to keep it consistent with _store.
            self._order.remove(key)
            # Line 34:  Signal successful deletion to the caller.
            return True
        # Line 36:  Key was not present, so signal failure (no-op).
        return False

    # Line 39:  Return a JSON-serializable snapshot of all memory (for debugging/logging).
    def snapshot(self):
        # Line 40:  Build a dict mapping each key to its value (excluding timestamps for brevity).
        return {k: v[0] for k, v in self._store.items()}
