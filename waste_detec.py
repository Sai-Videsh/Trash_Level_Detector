from cryptography.fernet import Fernet
import base64
import os
import firebase_admin
from firebase_admin import credentials, db
import datetime
import time
import RPi.GPIO as GPIO

# Firebase Admin SDK setup
cred = credentials.Certificate('/home/pi/Desktop/SAI_VIDESH_WDS/trash-level-5397d-firebase-adminsdk-fbsvc-93e77e529a.json')
firebase_admin.initialize_app(cred, {
    'databaseURL': 'https://trash-level-5397d-default-rtdb.firebaseio.com/'  # Correct URL
})
trash_ref = db.reference('trash_level')
history_ref = db.reference('trash_level_history')  # Reference for history

# GPIO Pin Setup for Ultrasonic Sensor, Buzzer, and 7-Segment Display
TRIG = 23
ECHO = 24
BUZZER = 17
SEG_A = 5
SEG_B = 6
SEG_C = 13
SEG_D = 19
SEG_E = 26
SEG_F = 21
SEG_G = 20
SEG_DP = 16

GPIO.setmode(GPIO.BCM)
GPIO.setup(TRIG, GPIO.OUT)
GPIO.setup(ECHO, GPIO.IN)
GPIO.setup(BUZZER, GPIO.OUT)

# Setup for 7-segment display
GPIO.setup([SEG_A, SEG_B, SEG_C, SEG_D, SEG_E, SEG_F, SEG_G, SEG_DP], GPIO.OUT, initial=GPIO.LOW)

MAX_LEVEL = 100
MIN_LEVEL = 15
current_level = 0
count_file = '/home/pi/current_level.txt'

# Segments configuration for display (L, P, A, F)
segment_map = {
    'L': [1, 0, 1, 0, 1, 0, 1],  # 'L'
    'P': [1, 1, 0, 1, 0, 1, 1],  # 'P'
    'A': [1, 1, 1, 0, 0, 1, 1],  # 'A'
    'F': [1, 1, 1, 1, 1, 0, 1]   # 'F'
}

# Key generation and loading
def generate_and_save_key():
    """Generate a new Fernet key and save it to a file."""
    key = Fernet.generate_key()
    with open("/home/pi/Desktop/SAI_VIDESH_WDS/secret.key", "wb") as key_file:
        key_file.write(key)
    print("New key generated and saved.")

def load_key():
    """Load the Fernet key from a file."""
    try:
        with open("/home/pi/Desktop/SAI_VIDESH_WDS/secret.key", "rb") as key_file:
            key = key_file.read()
        return key
    except FileNotFoundError:
        print("Key file not found. Please generate a new key.")
        return None

# Encrypt data using Fernet encryption
def encrypt_data(data):
    """Encrypt data using Fernet."""
    key = load_key()
    if key is None:
        print("Error: No valid key found.")
        return None
    cipher_suite = Fernet(key)
    encrypted_data = cipher_suite.encrypt(data.encode())  # Encrypt the data and return as bytes
    return base64.b64encode(encrypted_data).decode()  # Base64 encode to make it suitable for storage/transfer

# Decrypt data using Fernet encryption
def decrypt_data(encrypted_data):
    """Decrypt data using Fernet."""
    key = load_key()
    if key is None:
        print("Error: No valid key found.")
        return None
    cipher_suite = Fernet(key)
    encrypted_data = base64.b64decode(encrypted_data)  # Base64 decode the data
    decrypted_data = cipher_suite.decrypt(encrypted_data).decode()  # Decrypt and return as string
    return decrypted_data

def load_level():
    global current_level
    if os.path.exists(count_file):
        with open(count_file, 'r') as file:
            current_level = float(file.read().strip())
    else:
        current_level = 0.0
    print(f"Current Trash Level: {current_level}%")

def save_level():
    with open(count_file, 'w') as file:
        file.write(str(current_level))

def update_firebase_level():
    trash_ref.set({
        'level': current_level
    })
    print(f"Updated Firebase with trash level: {current_level}%")

def log_trash_level_history(level, weight=None, product_type=None):
    """Log the trash level with a timestamp, weight, and product type in Firebase history."""
    timestamp = datetime.datetime.utcnow().isoformat()  # Get current UTC time in ISO format
    
    # Prepare data to be encrypted
    history_data = {
        'level': level,
        'timestamp': timestamp
    }
    
    if weight is not None:
        history_data['weight'] = weight
    if product_type is not None:
        history_data['product_type'] = product_type
    
    # Encrypt the data
    encrypted_data = encrypt_data(str(history_data))  # Encrypt the entire history_data as a string
    
    if encrypted_data:
        # Push encrypted data to Firebase
        encrypted_history_data = {
            'encrypted_data': encrypted_data  # Store encrypted data
        }
        history_ref.push(encrypted_history_data)
        print(f"Logged encrypted trash level data: {history_data} at {timestamp}")

def increment_level_counter(level):
    """Increment the counter for the given level in Firebase."""
    if level == 15:
        trash_ref.child('reached_15_percent').transaction(lambda current_value: (current_value or 0) + 1)
    elif level == 70:
        trash_ref.child('reached_70_percent').transaction(lambda current_value: (current_value or 0) + 1)
    elif level == 90:
        trash_ref.child('reached_90_percent').transaction(lambda current_value: (current_value or 0) + 1)
    elif level == 100:
        trash_ref.child('reached_100_percent').transaction(lambda current_value: (current_value or 0) + 1)

def measure_distance():
    GPIO.output(TRIG, True)
    time.sleep(0.00001)
    GPIO.output(TRIG, False)
    
    while GPIO.input(ECHO) == 0:
        start_time = time.time()
        
    while GPIO.input(ECHO) == 1:
        end_time = time.time()

    duration = end_time - start_time
    measured_distance = (duration * 34300) / 2
    return round(measured_distance, 2)

def sound_buzzer(beep_duration=0.125, repeat=2):
    """Beep the buzzer `repeat` times, each for `beep_duration` seconds."""
    for _ in range(repeat):
        GPIO.output(BUZZER, GPIO.HIGH)
        time.sleep(beep_duration)
        GPIO.output(BUZZER, GPIO.LOW)
        time.sleep(0.125)

def continuous_buzzer(beep_duration=1):
    """Continuous beep for `beep_duration` seconds."""
    GPIO.output(BUZZER, GPIO.HIGH)
    time.sleep(beep_duration)
    GPIO.output(BUZZER, GPIO.LOW)

def display_segment(character):
    """Displays the given character on the 7-segment display."""
    GPIO.output([SEG_A, SEG_B, SEG_C, SEG_D, SEG_E, SEG_F, SEG_G], GPIO.LOW)
    for pin, state in zip([SEG_A, SEG_B, SEG_C, SEG_D, SEG_E, SEG_F, SEG_G], segment_map[character]):
        GPIO.output(pin, state)

def remove_trash():
    global current_level
    print("⚡️ Trash reached 100%. Trash level automatically reduced to 15%.")
    continuous_buzzer(beep_duration=2)  # Long beep for full trash can
    time.sleep(1)  # Let the buzzer sound for a second
    current_level = MIN_LEVEL  # Reset trash level to 15%
    increment_level_counter(15)  # Increment counter for 15%
    log_trash_level_history(current_level)  # Log the reset level

def update_trash_level(weight=None, product_type=None):
    global current_level
    current_level += 5  # Increment trash level by 5%
    if current_level >= MAX_LEVEL:
        display_segment('F')  # Display "Full" (F) on 7-segment display
        sound_buzzer(beep_duration=1, repeat=1)  # Long beep for "full"
        increment_level_counter(100)  # Increment counter for 100%
        log_trash_level_history(current_level, weight, product_type)  # Log the level at 100% with weight and type
        remove_trash()  # Reset trash level to 15%
    elif current_level >= 90:
        display_segment('A')  # Display "Almost full" (A)
        increment_level_counter(90)  # Increment counter for 90%
        log_trash_level_history(current_level, weight, product_type)  # Log the level at 90%
    elif current_level >= 70:
        display_segment('P')  # Display "Partial" (P)
        increment_level_counter(70)  # Increment counter for 70%
        log_trash_level_history(current_level, weight, product_type)  # Log the level at 70%
    else:
        display_segment('L')  # Display "Low" (L)
        log_trash_level_history(current_level, weight, product_type)  # Log the level at Low

    print(f"Trash level increased by 5%. New level: {current_level:.2f}%")

# Load the previous trash level when the script starts
load_level()

# Flag to prevent repeated Firebase updates
firebase_updated = False

try:
    while True:
        current_distance = measure_distance()

        if current_distance < 10:  # Object detected
            print("Object detected! Beeping now.")

            # Beep immediately when an object is detected
            sound_buzzer(beep_duration=0.5, repeat=1)

            # Ask for weight of the object
            weight = float(input("Enter the weight of the product in kg: "))

            # Ask if the product is biodegradable or not
            product_type = input("Is this product biodegradable or non-biodegradable? ").strip().lower()

            # Increase trash level by 5% when object is detected
            update_trash_level(weight, product_type)

            if current_level >= 100:
                # Continuous beep for full trash can
                continuous_buzzer(beep_duration=2)
            else:
                # Beep twice for 0.125 seconds each
                sound_buzzer(beep_duration=0.125, repeat=2)

            # Update Firebase if it hasn't been updated in this detection
            if not firebase_updated:
                save_level()
                update_firebase_level()
                firebase_updated = True  # Prevent further updates for this detection

        if current_distance >= 10 and firebase_updated:
            firebase_updated = False

        time.sleep(1)  # Adjust sleep time for sensor polling

except KeyboardInterrupt:
    GPIO.cleanup()
