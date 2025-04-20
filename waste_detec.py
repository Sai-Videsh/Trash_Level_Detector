from cryptography.fernet import Fernet
import base64
import os
import firebase_admin
from firebase_admin import credentials, db
import datetime
import time
import RPi.GPIO as GPIO

cred = credentials.Certificate('/home/pi/Desktop/SAI_VIDESH_WDS/trash-level-5397d-firebase-adminsdk-fbsvc-93e77e529a.json')
firebase_admin.initialize_app(cred, {
    'databaseURL': 'https://trash-level-5397d-default-rtdb.firebaseio.com/'
})
trash_ref = db.reference('trash_level')
history_ref = db.reference('trash_level_history')

# GPIO Pin Setup
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
GPIO.setup([SEG_A, SEG_B, SEG_C, SEG_D, SEG_E, SEG_F, SEG_G, SEG_DP], GPIO.OUT, initial=GPIO.LOW)

MAX_LEVEL = 100
MIN_LEVEL = 15
current_level = 0
count_file = '/home/pi/current_level.txt'

segment_map = {
    'L': [1, 0, 1, 0, 1, 0, 1],
    'P': [1, 1, 0, 1, 0, 1, 1],
    'A': [1, 1, 1, 0, 0, 1, 1],
    'F': [1, 1, 1, 1, 1, 0, 1]
}

def generate_and_save_key():
    key = Fernet.generate_key()
    with open("/home/pi/Desktop/SAI_VIDESH_WDS/secret.key", "wb") as key_file:
        key_file.write(key)
    print("New key generated and saved.")

def load_key():
    try:
        with open("/home/pi/Desktop/SAI_VIDESH_WDS/secret.key", "rb") as key_file:
            key = key_file.read()
        return key
    except FileNotFoundError:
        print("Key file not found. Please generate a new key.")
        return None

def encrypt_data(data):
    key = load_key()
    if key is None:
        print("Error: No valid key found.")
        return None
    cipher_suite = Fernet(key)
    encrypted_data = cipher_suite.encrypt(data.encode())
    return base64.b64encode(encrypted_data).decode()

def decrypt_data(encrypted_data):
    key = load_key()
    if key is None:
        print("Error: No valid key found.")
        return None
    cipher_suite = Fernet(key)
    encrypted_data = base64.b64decode(encrypted_data)
    decrypted_data = cipher_suite.decrypt(encrypted_data).decode()
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
    timestamp = datetime.datetime.utcnow().isoformat()
    
    history_data = {
        'level': level,
        'timestamp': timestamp
    }
    
    if weight is not None:
        history_data['weight'] = weight
    if product_type is not None:
        history_data['product_type'] = product_type
    
    encrypted_data = encrypt_data(str(history_data))
    
    if encrypted_data:
        encrypted_history_data = {
            'encrypted_data': encrypted_data
        }
        history_ref.push(encrypted_history_data)
        print(f"Logged encrypted trash level data: {history_data} at {timestamp}")

def increment_level_counter(level):
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

# Different buzzer patterns for various events
def sound_buzzer_pattern(pattern_type):
    if pattern_type == "object_detected":
        for duration in [0.05, 0.1, 0.15]:
            GPIO.output(BUZZER, GPIO.HIGH)
            time.sleep(duration)
            GPIO.output(BUZZER, GPIO.LOW)
            time.sleep(0.05)
    elif pattern_type == "trash_full":
        for _ in range(3):
            GPIO.output(BUZZER, GPIO.HIGH)
            time.sleep(0.15)
            GPIO.output(BUZZER, GPIO.LOW)
            time.sleep(0.1)
        for _ in range(3):
            GPIO.output(BUZZER, GPIO.HIGH)
            time.sleep(0.5)
            GPIO.output(BUZZER, GPIO.LOW)
            time.sleep(0.1)
        for _ in range(3):
            GPIO.output(BUZZER, GPIO.HIGH)
            time.sleep(0.15)
            GPIO.output(BUZZER, GPIO.LOW)
            time.sleep(0.1)
    elif pattern_type == "trash_reduced":
        for duration in [0.5, 0.3, 0.2]:
            GPIO.output(BUZZER, GPIO.HIGH)
            time.sleep(duration)
            GPIO.output(BUZZER, GPIO.LOW)
            time.sleep(0.1)
    elif pattern_type == "level_update":
        for _ in range(2):
            GPIO.output(BUZZER, GPIO.HIGH)
            time.sleep(0.125)
            GPIO.output(BUZZER, GPIO.LOW)
            time.sleep(0.125)

def display_segment(character):
    GPIO.output([SEG_A, SEG_B, SEG_C, SEG_D, SEG_E, SEG_F, SEG_G], GPIO.LOW)
    for pin, state in zip([SEG_A, SEG_B, SEG_C, SEG_D, SEG_E, SEG_F, SEG_G], segment_map[character]):
        GPIO.output(pin, state)

# Handle trash bin overflow
def remove_trash():
    global current_level
    print("⚡️ Trash reached 100%. Trash level automatically reduced to 15%.")
    sound_buzzer_pattern("trash_full")
    time.sleep(1)
    current_level = MIN_LEVEL
    increment_level_counter(15)
    log_trash_level_history(current_level)
    sound_buzzer_pattern("trash_reduced")

# Update trash level and handle threshold events
def update_trash_level(increment_amount, weight=None, product_type=None):
    global current_level
    
    old_level = current_level
    current_level += increment_amount
    
    if current_level > MAX_LEVEL:
        current_level = MAX_LEVEL
    
    print(f"Trash level increased by {increment_amount:.1f}%. New level: {current_level:.1f}%")
    
    if current_level >= MAX_LEVEL and old_level < MAX_LEVEL:
        display_segment('F')
        increment_level_counter(100)
        log_trash_level_history(current_level, weight, product_type)
        remove_trash()
    elif current_level >= 90 and old_level < 90:
        display_segment('A')
        increment_level_counter(90)
        log_trash_level_history(current_level, weight, product_type)
    elif current_level >= 70 and old_level < 70:
        display_segment('P')
        increment_level_counter(70)
        log_trash_level_history(current_level, weight, product_type)
    else:
        display_segment('L')
        log_trash_level_history(current_level, weight, product_type)

# Initialize system
load_level()

if current_level >= 100:
    display_segment('F')
elif current_level >= 90:
    display_segment('A')
elif current_level >= 70:
    display_segment('P')
else:
    display_segment('L')

# Main program loop
try:
    while True:
        print("\n===== SMART TRASH MONITORING SYSTEM =====")
        print(f"Current Trash Level: {current_level:.1f}%")
        print("1. Manual mode (fixed 5% increment)")
        print("2. Distance-based mode (increment based on distance)")
        choice = input("Choose mode (1 or 2): ")
        
        if choice == '1':
            print("Please place the object in front of the sensor...")
            object_detected = False
            
            for _ in range(30):
                distance = measure_distance()
                if distance < 10:
                    object_detected = True
                    sound_buzzer_pattern("object_detected")
                    print("Object detected!")
                    
                    weight = float(input("Enter the weight of the product in kg: "))
                    product_type = input("Is this product biodegradable or non-biodegradable? ").strip().lower()
                    
                    update_trash_level(5, weight, product_type)
                    sound_buzzer_pattern("level_update")
                    
                    save_level()
                    update_firebase_level()
                    break
                
                time.sleep(1)
                print(".", end="", flush=True)
            
            if not object_detected:
                print("\nNo object detected within timeout period.")
        
        elif choice == '2':
            print("Please place the object in front of the sensor...")
            object_detected = False
            
            for _ in range(30):
                distance = measure_distance()
                if distance < 10:
                    object_detected = True
                    sound_buzzer_pattern("object_detected")
                    print(f"Object detected at distance: {distance:.1f} cm!")
                    
                    increment_amount = min(10 + (10 - distance) * 9, 85)
                    
                    product_type = input("Is this product biodegradable or non-biodegradable? ").strip().lower()
                    
                    estimated_weight = (10 - distance) / 2
                    
                    update_trash_level(increment_amount, estimated_weight, product_type)
                    sound_buzzer_pattern("level_update")
                    
                    save_level()
                    update_firebase_level()
                    break
                
                time.sleep(1)
                print(".", end="", flush=True)
            
            if not object_detected:
                print("\nNo object detected within timeout period.")
        
        else:
            print("Invalid choice. Please enter 1 or 2.")

except KeyboardInterrupt:
    GPIO.cleanup()
    print("\nProgram terminated by user.")


'''Us sensor:
Vcc - 5v, gnd to gnd , trig to gpio 23 , actually to gpio24

Buzzer: 5v to 5v , gnd to gnd , control pin(relay) to gpio 17

# 7-Segment Display (Common Cathode):

# Segment A → GPIO 5 
# Segment B → GPIO 6 
# Segment C → GPIO 13 
# Segment D → GPIO 19 
# Segment E → GPIO 26 
# Segment F → GPIO 21 
# Segment G → GPIO 20 
# Decimal Point → GPIO 16 
# Common pin → Ground pin on Raspberry Pi '''
