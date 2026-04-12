from flask import Flask, render_template, request, redirect, url_for
from textblob import TextBlob
import sqlite3

def init_db():
    conn = sqlite3.connect('vibe_data.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_text TEXT NOT NULL,
            vibe TEXT NOT NULL,
            score REAL NOT NULL,
            length REAL NOT NULL
            )
    ''')
    
    conn.commit()
    conn.close()

init_db()

app = Flask(__name__)

class VibeAnalyzer:
    def analyze(self, text):
        if not text.strip():
            return "Empty", 0
        
        blob = TextBlob(text)
        score = blob.sentiment.polarity

        if score > 0.3:
            return "Positive sentiment! ❤️", score
        elif score < -0.3:
            return "Negative sentiment! 😞", score
        else:
            return "Neutral sentiment 👌", score

@app.route('/')
def home():
    return render_template('vibe.html')

@app.route('/analyze', methods=['POST'])
def analyze():
    user_input = request.form.get('user_text')
    model = VibeAnalyzer()
    vibe, score = model.analyze(user_input)
    char_count = len(user_input)
    display_percent = (score + 1) * 50

    if not user_input or not user_input.strip():
        return redirect(url_for('home'))
    
    if len(user_input) > 500:
        user_input = user_input[:500]

    try:
        conn = sqlite3.connect('vibe_data.db')
        cursor = conn.cursor()
        cursor.execute("INSERT INTO history (user_text, vibe, score, length) VALUES (?, ?, ?, ?)", 
                    (user_input, vibe, round(score, 2), int(char_count)))
        conn.commit()
    except sqlite3.Error as e:
        print(f"Database error: {e}")
    finally:
        if conn:
            conn.close()

    return render_template('vibe.html', user_input=user_input, result=vibe, score=round(score, 2), percent=display_percent)

@app.route('/history')
def history():
    conn = sqlite3.connect('vibe_data.db')
    conn.row_factory = sqlite3.Row
    
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM history ORDER BY id DESC")
    
    db_rows = cursor.fetchall()
    
    conn.close()
    
    return render_template('vibe.html', history=db_rows)

@app.route('/clear')
def clear_history():
    conn = sqlite3.connect('vibe_data.db')
    cursor = conn.cursor()

    cursor.execute("DELETE FROM history")

    conn.commit()
    conn.close()
    
    return redirect(url_for('home'))

@app.route('/back')
def back():
    return redirect(url_for('home'))

@app.route('/stats')
def stats():
    conn = sqlite3.connect('vibe_data.db')
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM history")
    total_vibes = cursor.fetchone()[0]

    cursor.execute("SELECT AVG(score) FROM history")
    avg_score = cursor.fetchone()[0] or 0

    cursor.execute("SELECT COUNT(*) FROM history WHERE vibe = 'Positive sentiment! ❤️'")
    pos_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM history WHERE vibe = 'Negative sentiment! 😞'")
    neg_count = cursor.fetchone()[0]

    conn.close()

    if total_vibes > 0:
        pos_percent = (pos_count / total_vibes) * 100
        neg_percent = (neg_count / total_vibes) * 100
    else:
        pos_percent = neg_percent = 0

    return render_template('stats.html', 
                           total=total_vibes, 
                           avg=round(avg_score, 2),
                           pos_p=round(pos_percent, 1),
                           neg_p=round(neg_percent, 1))

if __name__ == "__main__":
    app.run(debug=True)