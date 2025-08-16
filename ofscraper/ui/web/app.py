from flask import Flask, render_template, request, jsonify
from flask_sse import sse
import threading
import time
from ofscraper.ui.api import build_scrape_context, run_scraper, update_queue, get_progress

app = Flask(__name__)
app.config["REDIS_URL"] = "redis://localhost"  # Adjust if using Redis for SSE
app.register_blueprint(sse, url_prefix='/stream')

scrape_thread = None
monitor_thread = None
running = False

def publish_progress(message):
    with app.app_context():
        sse.publish({"message": message}, type='progress')

def monitor_updates():
    global running
    while running:
        try:
            msg = update_queue.get(timeout=1)
            publish_progress(msg)
        except Exception:
            pass
        time.sleep(0.1)  # Small delay to avoid CPU overload

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/start', methods=['POST'])
def start_scrape():
    global scrape_thread, monitor_thread, running
    if running:
        return "Scraping already in progress", 400

    inputs = {
        'api_key': request.form.get('api_key'),
        'profiles': request.form.get('profile_url').split(','),
        'actions': request.form.getlist('actions'),
        'scrape_paid': 'scrape_paid' in request.form,
        'download_options': {
            'folder': request.form.get('download_folder'),
            # Add sliders, checkboxes values
            'max_count': int(request.form.get('max_count', 0)),
            'size_min': int(request.form.get('size_min', 0)),
            'size_max': int(request.form.get('size_max', 0)),
            # etc.
        }
    }
    context = build_scrape_context(inputs)
    scrape_thread, _ = run_scraper(context, publish_progress)
    running = True
    monitor_thread = threading.Thread(target=monitor_updates)
    monitor_thread.start()
    return "Scraping started"

@app.route('/cancel', methods=['POST'])
def cancel_scrape():
    global running
    running = False
    # Signal to stop scraping if possible
    return "Scraping cancelled"

@app.route('/progress')
def progress():
    return render_template('progress.html')

@app.route('/status')
def status():
    if not running:
        return jsonify({'progress': 0, 'status': 'idle'})
    progress = get_progress()
    return jsonify({'progress': progress, 'status': 'running'})

@app.route('/results')
def results():
    # Assuming results are stored somewhere, e.g., a global list or file
    results = []  # Placeholder: fetch results
    return render_template('results.html', results=results)

@app.route('/settings', methods=['GET', 'POST'])
def settings():
    if request.method == 'POST':
        # Save settings, perhaps update config
        pass
    return render_template('settings.html')

@app.route('/export')
def export():
    # Generate CSV and return
    return "CSV content", 200, {'Content-Type': 'text/csv', 'Content-Disposition': 'attachment; filename=results.csv'}

if __name__ == '__main__':
    app.run(debug=True)