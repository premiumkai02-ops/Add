from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from functools import wraps
from config import Config
from userbot import UserbotManager
import asyncio
import logging
import threading
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = Config.SECRET_KEY

userbot = UserbotManager()

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session:
            flash('សូមចូលប្រើប្រាស់ជាមុនសិន!', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def run_async(coroutine):
    """ដំណើរការ Async Function"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coroutine)
    finally:
        loop.close()

@app.route('/')
def index():
    if 'logged_in' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if username == Config.ADMIN_USERNAME and password == Config.ADMIN_PASSWORD:
            session['logged_in'] = True
            session['username'] = username
            flash('ចូលប្រើប្រាស់ដោយជោគជ័យ!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('ឈ្មោះអ្នកប្រើ ឬពាក្យសម្ងាត់មិនត្រឹមត្រូវ!', 'error')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('បានចាកចេញពីប្រព័ន្ធ!', 'success')
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    status = userbot.get_status()
    return render_template('dashboard.html', status=status)

@app.route('/scrape-members', methods=['GET', 'POST'])
@login_required
def scrape_members():
    if request.method == 'POST':
        source_group = request.form.get('source_group')
        limit = int(request.form.get('limit', 100))
        search_keyword = request.form.get('search_keyword', '')
        
        if not source_group:
            flash('សូមបញ្ចូល Group ប្រភព!', 'error')
            return redirect(url_for('scrape_members'))
        
        try:
            if not userbot.is_running:
                run_async(userbot.start())
            
            members = run_async(userbot.scrape_members(
                source_group=source_group,
                limit=limit,
                search_keyword=search_keyword if search_keyword else None
            ))
            
            flash(f'ទាញសមាជិកបាន {len(members)} នាក់!', 'success')
            
            return render_template(
                'scrape_members.html',
                members=members[:50],
                total=len(members)
            )
            
        except Exception as e:
            flash(f'មានបញ្ហា: {str(e)}', 'error')
            return redirect(url_for('scrape_members'))
    
    return render_template('scrape_members.html', members=None)

@app.route('/auto-add', methods=['GET', 'POST'])
@login_required
def auto_add():
    if request.method == 'POST':
        source_group = request.form.get('source_group')
        limit = int(request.form.get('limit', 50))
        delay = int(request.form.get('delay', 3))
        
        if not source_group:
            flash('សូមបញ្ចូល Group ប្រភព!', 'error')
            return redirect(url_for('auto_add'))
        
        try:
            if not userbot.is_running:
                run_async(userbot.start())
            
            stats = run_async(userbot.scrape_and_add(
                source_group=source_group,
                limit=limit,
                delay=delay
            ))
            
            flash('ប្រតិបត្តិការបានបញ្ចប់!', 'success')
            return render_template('auto_add.html', stats=stats)
            
        except Exception as e:
            flash(f'មានបញ្ហា: {str(e)}', 'error')
            return redirect(url_for('auto_add'))
    
    return render_template('auto_add.html', stats=None)

@app.route('/add-scraped', methods=['POST'])
@login_required
def add_scraped():
    if not userbot.scraped_members:
        flash('មិនមានសមាជិកដែលបានទាញទេ!', 'error')
        return redirect(url_for('scrape_members'))
    
    delay = int(request.form.get('delay', 3))
    
    try:
        stats = run_async(userbot.add_members_to_group(
            members=userbot.scraped_members,
            delay=delay
        ))
        
        flash('បន្ថែមសមាជិកបានបញ្ចប់!', 'success')
        return render_template('auto_add.html', stats=stats)
        
    except Exception as e:
        flash(f'មានបញ្ហា: {str(e)}', 'error')
        return redirect(url_for('scrape_members'))

@app.route('/api/status')
@login_required
def api_status():
    return jsonify(userbot.get_status())

@app.route('/start-userbot', methods=['POST'])
@login_required
def start_userbot():
    try:
        if not userbot.is_running:
            run_async(userbot.start())
            flash('Userbot បានចាប់ផ្តើម!', 'success')
        else:
            flash('Userbot កំពុងដំណើរការរួចហើយ!', 'info')
    except Exception as e:
        flash(f'មានបញ្ហា: {str(e)}', 'error')
    
    return redirect(url_for('dashboard'))

@app.route('/stop-userbot', methods=['POST'])
@login_required
def stop_userbot():
    try:
        if userbot.is_running:
            run_async(userbot.stop())
            flash('Userbot បានបញ្ឈប់!', 'success')
    except Exception as e:
        flash(f'មានបញ្ហា: {str(e)}', 'error')
    
    return redirect(url_for('dashboard'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=Config.PORT, debug=False)
