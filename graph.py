import firebase_admin
from firebase_admin import credentials, db
import matplotlib.pyplot as plt
from collections import Counter
import datetime
import sqlite3
import pandas as pd
from cryptography.fernet import Fernet
import base64
import json

# Generate and store the encryption key securely (for demo purposes, using a static key)
ENCRYPTION_KEY = b'GKMv5Xd7yIC2NoB9EjJ0uV2y-tyPBJg41Uj1iz5BvVk='
cipher_suite = Fernet(ENCRYPTION_KEY)

# Firebase Admin SDK setup
cred = credentials.Certificate(r'C:\Users\saivi\OneDrive\Desktop\My folder\Academics\ESIOT\Trash_Level\trash-level-5397d-firebase-adminsdk-fbsvc-93e77e529a.json');
firebase_admin.initialize_app(cred, {
    'databaseURL': 'https://trash-level-5397d-default-rtdb.firebaseio.com/'
})

history_ref = db.reference('trash_level_history')

# Connect to SQLite database (or create if it doesn't exist)
conn = sqlite3.connect('trash_data.db')
cursor = conn.cursor()

# Create table if it doesn't exist
cursor.execute('''CREATE TABLE IF NOT EXISTS trash_data (
                    id TEXT PRIMARY KEY,
                    level INTEGER,
                    weight REAL,
                    product_type TEXT,
                    timestamp TEXT
                )''')
conn.commit()


# def store_trash_data(record_id, data):
#     encrypted_data = {
#         "level": encrypt_data(str(data["level"])),  
#         "weight": encrypt_data(str(data["weight"])),
#         "product_type": encrypt_data(data["product_type"])
#     }
#     history_ref.child(record_id).set(encrypted_data)

def encrypt_data(data):
    json_data = json.dumps(data)
    encrypted_data = cipher_suite.encrypt(json_data.encode())
    return base64.urlsafe_b64encode(encrypted_data).decode()

# Decrypt data after retrieving from Firebase
def decrypt_data(encrypted_data):
    try:
        if isinstance(encrypted_data, dict):  
            return encrypted_data  # Data is already in JSON format
        decrypted_data = cipher_suite.decrypt(base64.urlsafe_b64decode(encrypted_data.encode()))
        return json.loads(decrypted_data.decode())
    except Exception as e:
        print(f"Decryption Error: {e}")
        return None


def get_firebase_data():
    encrypted_data = history_ref.get()
    if encrypted_data:
        decrypted_records = {key: decrypt_data(value) for key, value in encrypted_data.items() if decrypt_data(value) is not None}

        for record_id, record in decrypted_records.items():
            cursor.execute('''INSERT OR REPLACE INTO trash_data (id, level, weight, product_type, timestamp) 
                              VALUES (?, ?, ?, ?, ?)''', 
                           (record_id, record.get('level', None), record.get('weight', None), 
                            record.get('product_type', None), record.get('timestamp', None)))
        conn.commit()
        return decrypted_records
    return {}


def load_excel_data():
    return pd.read_excel('trash_data_1.xlsx')

def plot_trash_level_bargraph():
    df = load_excel_data()

    # Convert 'level' column to numeric, forcing errors to NaN, then dropping NaN values
    df['level'] = pd.to_numeric(df['level'], errors='coerce')
    df = df.dropna(subset=['level'])  # Remove rows with invalid data in 'level' column
    df['level'] = df['level'].astype(int)  # Convert to integer type

    trash_level_counts = df['level'].value_counts().sort_index()

    plt.figure(figsize=(6, 4))
    plt.bar(trash_level_counts.index, trash_level_counts.values, color='skyblue')
    plt.xlabel('Trash Level (%)')
    plt.ylabel('Number of Times Reached')
    plt.title('Number of Times Each Trash Level is Reached')
    plt.show()


def count_overflows():
    df = load_excel_data()
    overflow_count = (df['level'] == 100).sum()
    # print(f"Number of times the trash bin overflowed: 5{overflow_count}")

def plot_bio_nonbio_pie_chart():
    df = load_excel_data()
    product_types = ['bio', 'non-bio']
    counts = [df[df['product_type'].str.lower() == p].shape[0] for p in product_types]

    labels = ['Biodegradable', 'Non-Biodegradable']
    colors = ['#ff9999', '#66b3ff']

    plt.figure(figsize=(6, 6))
    plt.pie(counts, labels=labels, autopct='%1.1f%%', startangle=60, colors=colors, wedgeprops={'linewidth': 1, 'edgecolor': 'black'})
    plt.title('Biodegradable vs Non-Biodegradable Waste')
    plt.axis('equal')
    plt.tight_layout()
    plt.show()



def plot_weight_vs_frequency():
    df = load_excel_data()
    
    # Convert 'weight' column to numeric, forcing errors to NaN, then drop NaN values
    df['weight'] = pd.to_numeric(df['weight'], errors='coerce')
    df = df.dropna(subset=['weight'])
    
    # Convert to integers before grouping
    df['weight_rounded'] = (df['weight'] // 50) * 50
    
    weight_counts = df['weight_rounded'].value_counts().sort_index()
    plt.figure(figsize=(6, 4))
    plt.plot(weight_counts.index, weight_counts.values, marker='o', linestyle='-', color='blue')
    plt.xlabel('Weight (kg)')
    plt.ylabel('Number of Times Collected')
    plt.title('Weight vs Number of Times Object Collected')
    plt.grid(True)
    plt.show()


if __name__ == '__main__':
    get_firebase_data()  # Fetch data from Firebase to store in SQLite
    plot_trash_level_bargraph()
    count_overflows()
    plot_bio_nonbio_pie_chart()
    plot_weight_vs_frequency()

