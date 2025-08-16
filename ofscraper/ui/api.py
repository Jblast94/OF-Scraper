import threading
import logging
import queue
from types import SimpleNamespace
from ofscraper.commands.scraper.scraper import scraperManager
from ofscraper.commands.utils.scrape_context import scrape_context_manager
from ofscraper.utils.args.mutators.write import setArgs
from ofscraper.utils.settings import update_args
from ofscraper.utils.live.updater import download, activity  # For progress integration

# Queue for progress and log updates
update_queue = queue.Queue()

# Custom logging handler to push logs to queue
class QueueHandler(logging.Handler):
    def emit(self, record):
        update_queue.put(self.format(record))

# Setup logger
logger = logging.getLogger("ofscraper")
queue_handler = QueueHandler()
logger.addHandler(queue_handler)

def build_scrape_context(inputs):
    """Builds and returns a ScrapeContext based on UI inputs with error handling."""
    try:
        args_dict = {
            'actions': inputs.get('actions', []),
            'scrape_paid': inputs.get('scrape_paid', False),
            'users': inputs.get('profiles', []),
            'download': inputs.get('download_options', {}),
            # Map more inputs as needed
        }
        args = SimpleNamespace(**args_dict)
        setArgs(args)
        update_args(args)
        return args
    except Exception as e:
        logger.error(f"Error building scrape context: {str(e)}")
        raise  # Propagate error for UI to handle

def run_scraper(context, progress_callback=None, log_callback=None):
    """
    Runs the scraper in a background thread with optional callbacks and error handling.

    Args:
        context: The scrape context built from inputs.
        progress_callback: Function to call on progress updates.
        log_callback: Function to call on log messages.

    Returns:
        tuple: (scrape_thread, monitor_thread)
    """
    try:
        if progress_callback:
            progress_observer.add_callback(progress_callback)
        if log_callback:
            log_observer.add_callback(log_callback)

        def target():
            try:
                with scrape_context_manager():
                    manager = scraperManager()
                    manager.runner()
            except Exception as e:
                logger.error(f"Error during scraper execution: {str(e)}")
                update_queue.put(f"Error: {str(e)}")  # Send error to UI queue
                raise  # Propagate for UI handling

        thread = threading.Thread(target=target)
        thread.start()
        monitor_thread = threading.Thread(target=lambda: thread.join())
        monitor_thread.start()
        return thread, monitor_thread
    except Exception as e:
        logger.error(f"Failed to start scraper: {str(e)}")
        raise

# Function to get progress (for polling if needed)
def get_progress():
    # Example: return current download progress
    task_id = download.job.tasks[0].id if download.job.tasks else None
    if task_id:
        task = download.job.get_task(task_id)
        return task.completed / task.total if task.total else 0
    return 0