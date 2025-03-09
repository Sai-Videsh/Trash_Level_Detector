import firebase_admin
from firebase_admin import credentials, db
import matplotlib.pyplot as plt
from collections import Counter
import datetime

# Firebase Admin SDK setup
cred = credentials.Certificate('/home/pi/Desktop/SAI_VIDESH_WDS/trash-level-5397d-firebase-adminsdk-fbsvc-93e77e529a.json')
firebase_admin.initialize_app(cred, {
    'databaseURL': 'https://trash-level-5397d-default-rtdb.firebaseio.com/'  # Correct URL
})

history_ref = db.reference('trash_level_history')  # Reference for history

# Retrieve data from Firebase
def get_firebase_data():
    # Fetch all history records from Firebase
    history_data = history_ref.get()
    return history_data

# 1. Bar Graph for number of times a particular % is reached (15%, 70%, 90%, 100%)
def plot_trash_level_bargraph():
    history_data = get_firebase_data()
    
    # Count occurrences of trash levels
    trash_level_counts = Counter()
    for record in history_data.values():
        if 'level' in record:
            level = record['level']
            if level in [15, 70, 90, 100]:
                trash_level_counts[level] += 1
    
    # Plot the bar graph
    levels = [15, 70, 90, 100]
    counts = [trash_level_counts[level] for level in levels]

    plt.bar(levels, counts, color='skyblue')
    plt.xlabel('Trash Level (%)')
    plt.ylabel('Number of Times Reached')
    plt.title('Number of Times Each Trash Level is Reached')
    plt.xticks(levels)
    plt.show()

# 2. Number of times the trash bin overflowed (Reached 100%)
def count_overflows():
    history_data = get_firebase_data()
    
    overflow_count = 0
    for record in history_data.values():
        if 'level' in record and record['level'] == 100:
            overflow_count += 1
    
    print(f"Number of times the trash bin overflowed: {overflow_count}")

# 3. Pie Chart for Biodegradable vs Non-Biodegradable
def plot_bio_nonbio_pie_chart():
    history_data = get_firebase_data()
    
    bio_count = 0
    non_bio_count = 0
    
    for record in history_data.values():
        if 'product_type' in record:
            product_type = record['product_type'].lower()
            if product_type == 'bio':
                bio_count += 1
            elif product_type == 'non-bio':
                non_bio_count += 1
    
    # Plot pie chart
    labels = 'Biodegradable', 'Non-Biodegradable'
    sizes = [bio_count, non_bio_count]
    colors = ['lightgreen', 'lightcoral']
    plt.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%', startangle=90)
    plt.title('Biodegradable vs Non-Biodegradable Trash')
    plt.axis('equal')  # Equal aspect ratio ensures the pie chart is a circle
    plt.show()

# 4. Line Graph for Weight vs Frequency of Collection (Thresholding weight)
def plot_weight_vs_frequency():
    history_data = get_firebase_data()
    
    # Dictionary to count weights (rounded off as required)
    weight_counts = {}
    
    for record in history_data.values():
        if 'weight' in record:
            weight = record['weight']
            # Thresholding and rounding off weight (based on your requirement)
            rounded_weight = int(round(weight / 50) * 50)  # Adjust the scale of 50kg as a threshold
            if rounded_weight in weight_counts:
                weight_counts[rounded_weight] += 1
            else:
                weight_counts[rounded_weight] = 1
    
    # Prepare the data for plotting
    weights = sorted(weight_counts.keys())
    frequencies = [weight_counts[weight] for weight in weights]
    
    # Plot the normal line graph
    plt.plot(weights, frequencies, marker='o')
    plt.xlabel('Weight (kg)')
    plt.ylabel('Number of Times Collected')
    plt.title('Weight vs Number of Times Object Collected')
    plt.grid(True)
    plt.show()

# Call the functions to plot the graphs
if __name__ == '__main__':
    plot_trash_level_bargraph()  # Plot the bar graph for trash levels
    count_overflows()  # Count the number of overflows
    plot_bio_nonbio_pie_chart()  # Plot the pie chart for biodegradable vs non-biodegradable
    plot_weight_vs_frequency()  # Plot the weight vs frequency graph
