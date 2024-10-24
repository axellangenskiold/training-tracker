import matplotlib.pyplot as plt
from collections import Counter

def read_data_from_file(filename):
    data = []
    try:
        with open(filename, 'r') as file:
            for line in file:
                data.append(line.strip())
    except FileNotFoundError:
        print(f"Error: File '{filename}' not found.")
    except IOError:
        print(f"Error: Unable to read file '{filename}'.")
    return data

# Read data from data.txt
filename = "data.txt"
data = read_data_from_file(filename)

# Parse data
dates = []
weights = []
distances = []
activities = []

year = None

for item in data:
    if item[0] == "Y":
        year = item[1:]
    else:
        date, rest = item.split(":")
        day, month, year = date.split("/") + [year]
        
        # Split rest and check if it has two parts
        rest_parts = rest.split(",")
        if len(rest_parts) == 2:
            activity, weightOrDistance = rest_parts
        else:
            activity, weightOrDistance = rest, None
        
        if weightOrDistance == None:
            weightOrDistance = weights[-1]
        elif weightOrDistance == "run" or weightOrDistance == "löpning":
            distances.append(weightOrDistance[:-2])
            weightOrDistance = weights[-1]
            
        
        # Assuming weight is the second part of the split
        weight = float(weightOrDistance[:-2])
        full_date = f"{day}/{month}/{year}"
        
        dates.append(full_date)
        weights.append(weight)
        activities.append(activity.strip())

# Plot data
plt.figure(figsize=(10, 6))

# Create a color map for activities
activity_colors = {activity: f"C{i}" for i, activity in enumerate(set(activities))}

# Plot each point with the corresponding activity color
for date, weight, activity in zip(dates, weights, activities):
    plt.scatter(date, weight, color=activity_colors[activity], label=activity)

# Add legend for activities
activity_counts = Counter(activities)
legend_labels = [f"{activity} ({count})" for activity, count in activity_counts.items()]
plt.legend(legend_labels, loc='upper right')

# Set labels and title
plt.xlabel('Date')
plt.ylabel('Weight')
plt.title('Weight Over Time with Activities')

# Set x-ticks to show every 10th date, including the first and last
x_ticks = [dates[0]] + dates[9::10] + [dates[-1]]
plt.xticks(x_ticks, rotation=45)

# Show plot
plt.tight_layout()
plt.show()
