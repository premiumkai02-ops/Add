import sqlite3
import json
from datetime import datetime
from config import Config

class Database:
    def __init__(self):
        self.conn = sqlite3.connect(Config.DATABASE_PATH, check_same_thread=False)
        self.create_tables()
    
    def create_tables(self):
        """បង្កើតតារាងទិន្នន័យ"""
        cursor = self.conn.cursor()
        
        # តារាងសម្រាប់រក្សាទុកសមាជិកដែលបានបន្ថែម
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS added_members (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT,
                username TEXT,
                first_name TEXT,
                last_name TEXT,
                added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                status TEXT DEFAULT 'success'
            )
        ''')
        
        # តារាងសម្រាប់រក្សាទុកស្ថិតិ
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS stats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                total_scraped INTEGER DEFAULT 0,
                total_added INTEGER DEFAULT 0,
                failed INTEGER DEFAULT 0,
                skipped INTEGER DEFAULT 0,
                flood_waits INTEGER DEFAULT 0,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        self.conn.commit()
    
    def add_member(self, user_data):
        """បន្ថែមសមាជិកទៅក្នុងតារាង"""
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO added_members (user_id, username, first_name, last_name)
            VALUES (?, ?, ?, ?)
        ''', (
            str(user_data.get('id', '')),
            user_data.get('username', ''),
            user_data.get('first_name', ''),
            user_data.get('last_name', '')
        ))
        self.conn.commit()
    
    def get_added_members(self, limit=10):
        """ទាញយកសមាជិកដែលបានបន្ថែម"""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT * FROM added_members 
            ORDER BY added_at DESC 
            LIMIT ?
        ''', (limit,))
        columns = [description[0] for description in cursor.description]
        results = []
        for row in cursor.fetchall():
            results.append(dict(zip(columns, row)))
        return results
    
    def update_stats(self, stats_data):
        """ធ្វើបច្ចុប្បន្នភាពស្ថិតិ"""
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO stats (total_scraped, total_added, failed, skipped, flood_waits)
            VALUES (?, ?, ?, ?, ?)
        ''', (
            stats_data.get('total_scraped', 0),
            stats_data.get('total_added', 0),
            stats_data.get('failed', 0),
            stats_data.get('skipped', 0),
            stats_data.get('flood_waits', 0)
        ))
        self.conn.commit()
    
    def get_latest_stats(self):
        """ទាញយកស្ថិតិចុងក្រោយ"""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT * FROM stats 
            ORDER BY updated_at DESC 
            LIMIT 1
        ''')
        row = cursor.fetchone()
        if row:
            columns = [description[0] for description in cursor.description]
            return dict(zip(columns, row))
        return None
    
    def close(self):
        """បិទការភ្ជាប់ Database"""
        self.conn.close()
