import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import mplcursors
from collections import Counter
from datetime import datetime

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
distances = {}
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
        
        # Strip whitespace from activity
        activity = activity.strip()
        
        if weightOrDistance == None:
            weightOrDistance = weights[-1]
        elif activity == 'run' or activity == "löpning":
            distances[len(activities)] = (float(weightOrDistance[:-2]))
            weightOrDistance = weights[-1]
        else:
            weightOrDistance = float(weightOrDistance[:-2])
            
        

        full_date = f"{day}/{month}/{year}"
        
        dates.append(full_date)
        weights.append(weightOrDistance)
        activities.append(activity.strip())

# Convert date strings to datetime objects
dates = [datetime.strptime(date, '%d/%m/%Y') for date in dates]

# Plot data
plt.figure(figsize=(10, 6))

# Create a color map for activities
activity_colors = {activity: f"C{i}" for i, activity in enumerate(set(activities))}

# Add a line plot to connect the points
line, = plt.plot(dates, weights, linestyle='-', color='red', alpha=0.5)

# Plot each point with the corresponding activity color
scatter = plt.scatter(dates, weights, c=[activity_colors[activity] for activity in activities])

# Add interactive cursor with hover functionality on the scatter plot
cursor = mplcursors.cursor(scatter, hover=True)
cursor.connect(
    "add", lambda sel: sel.annotation.set(
        text=(
            f"Date: {dates[sel.index].strftime('%Y-%m-%d')}\n"
            f"Activity: {activities[sel.index]}\n"
            f"Weight: {weights[sel.index]} kg\n"
            + (f"Distance: {distances[sel.index]} km" if activities[sel.index] in ['löpning', 'run'] else "")
        ),
        position=(0, -50),  # Adjust the position offset here
        anncoords="offset points"
    )
)

# Calculate the number of activities, number of days, and total kilometers
num_activities = len(activities)
start_date = min(dates)
num_days = (max(dates) - start_date).days
total_kilometers = sum(distances.values())

# Add legend for activities with additional summary information
activity_counts = Counter(activities)
legend_labels = [f"{activity} ({count})" for activity, count in activity_counts.items()]
summary_label = f"Consistency: {num_activities}/{num_days} days\nTotal km: {total_kilometers:.2f}"

plt.legend(
    handles=[
        plt.Line2D([0], [0], marker='o', color='w', label=label,
                   markerfacecolor=activity_colors[activity], markersize=10)
        for activity, label in zip(activity_counts.keys(), legend_labels)
    ] + [plt.Line2D([0], [0], color='w', label=summary_label)],
    loc='upper right'
)

# Set labels and title
plt.xlabel('Date')
plt.ylabel('Weight (kg)')  # Updated y-axis label

# Set y-axis limits from the lowest to the highest weight
plt.ylim(min(weights) -2, max(weights) + 2)  # Set y-axis limits

plt.title('Weight Over Time with Activities')

# Set x-ticks to show every 10th date, including the first and last
x_ticks = [dates[0]] + dates[3::4] + [dates[-1]]
plt.xticks(x_ticks, rotation=45)

# Show plot
plt.tight_layout()
plt.show()




