from flask import Flask, render_template, request, redirect, url_for, jsonify, send_from_directory
import os, random, hashlib
from werkzeug.utils import secure_filename
import matplotlib.pyplot as plt
import numpy as np
import uuid
import json

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['CHART_FOLDER'] = 'static/charts'
# Buat folder upload & chart kalau belum ada
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['CHART_FOLDER'], exist_ok=True)

LEADERBOARD_FILE = 'leaderboard.json'

# Buat file JSON jika belum ada
if not os.path.exists(LEADERBOARD_FILE):
    with open(LEADERBOARD_FILE, 'w') as f:
        json.dump([], f)

def load_leaderboard():
    with open(LEADERBOARD_FILE, 'r') as f:
        return json.load(f)

def save_leaderboard(name, photo, stats):
    leaderboard = []
    if os.path.exists(LEADERBOARD_FILE):
        with open(LEADERBOARD_FILE, 'r') as f:
            try:
                leaderboard = json.load(f)
            except json.JSONDecodeError:
                leaderboard = []

    # Buang semua data dengan nama yang sama
    leaderboard = [entry for entry in leaderboard if entry['name'] != name]

    # Tambahkan data baru untuk setiap kategori
    for category, value in stats.items():
        leaderboard.append({
            'name': name,
            'photo': photo,
            'category': category,
            'value': value
        })

    # Simpan kembali
    with open(LEADERBOARD_FILE, 'w') as f:
        json.dump(leaderboard, f, indent=2)
        
        
from flask import send_from_directory

@app.route('/static/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/static/charts/<filename>')
def chart_file(filename):
    return send_from_directory(app.config['CHART_FOLDER'], filename)
    


def generate_stats(name):
    hash_seed = int(hashlib.md5(name.encode()).hexdigest(), 16)
    random.seed(hash_seed)
    stats = {
        'KARBIT': random.randint(0, 100),
        'GAY': random.randint(0, 100),
        'SEPUH': random.randint(0, 100),
        'CERDAS': random.randint(0, 100),
        'SARAN_TEKS': random.randint(0, 100),
        'SARAN TEKS': random.randint(0, 100)
    }
    return stats

def save_radar_chart(stats, name):
    labels = list(stats.keys())  # 6 label
    values = list(stats.values())  # 6 nilai

    angles = np.linspace(0, 2 * np.pi, len(labels), endpoint=False).tolist()
    
    # Tutup loop
    values += values[:1]
    angles += angles[:1]

    fig, ax = plt.subplots(figsize=(4, 4), subplot_kw=dict(polar=True))
    ax.plot(angles, values, color='cyan', linewidth=2)
    ax.fill(angles, values, color='cyan', alpha=0.3)

    ax.set_yticklabels([])  # sembunyikan nilai radial
    ax.set_xticks(np.linspace(0, 2 * np.pi, len(labels), endpoint=False))
    ax.set_xticklabels(labels)  # cuma 6 label, cocok

    ax.set_facecolor('black')
    fig.patch.set_facecolor('black')
    plt.tight_layout()

    filename = f"{hashlib.md5(name.encode()).hexdigest()}.png"
    path = os.path.join(app.config['CHART_FOLDER'], filename)
    plt.savefig(path, transparent=True)
    plt.close(fig)
    return filename
    
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/result', methods=['POST'])
def result():
    name = request.form['name']
    photo = request.files['photo']
    filename = secure_filename(photo.filename)
    photo.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

    stats = generate_stats(name)
    leaderboard = load_leaderboard()
    for category, value in stats.items():
        leaderboard.append({
            'name': name,
            'photo': filename,
            'category': category,
            'value': value
        })
    save_leaderboard(name, filename, stats)
    chart_filename = save_radar_chart(stats, name)
    return render_template('result.html', name=name, filename=filename,
                           chart_filename=chart_filename, stats=stats)

@app.route('/leaderboard')
def leaderboard():
    category = request.args.get('category', 'KARBIT')
    leaderboard = load_leaderboard()
    filtered = [entry for entry in leaderboard if entry['category'] == category]
    sorted_entries = sorted(filtered, key=lambda x: x['value'], reverse=True)[:10]
    return render_template('leaderboard.html', category=category, rows=sorted_entries)
    
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=False, host='0.0.0.0', port=port)
