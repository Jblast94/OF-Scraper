from typing import Callable, List

class Observer:
    def __init__(self):
        self.callbacks: List[Callable] = []

    def add_callback(self, cb: Callable):
        self.callbacks.append(cb)

    def remove_callback(self, cb: Callable):
        if cb in self.callbacks:
            self.callbacks.remove(cb)

    def notify(self, *args, **kwargs):
        for cb in self.callbacks:
            try:
                cb(*args, **kwargs)
            except Exception as e:
                # Log error or handle
                pass

progress_observer = Observer()
log_observer = Observer()