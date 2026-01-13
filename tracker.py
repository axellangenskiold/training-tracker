import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from collections import Counter
from datetime import datetime, timedelta
import subprocess
import platform
from matplotlib.widgets import RangeSlider

def read_data_from_file(filename):
    """Reads data from a file, skipping the first line."""
    data = []
    try:
        with open(filename, 'r') as file:
            next(file)  # Skip the first line
            for line in file:
                data.append(line.strip())
    except FileNotFoundError:
        print(f"Error: File '{filename}' not found.")
    except IOError:
        print(f"Error: Unable to read file '{filename}'.")
    return data

def get_note_content(note_title):
    """Retrieves the content of a note from the Notes app using AppleScript."""
    
    if platform.system() != 'Darwin':
        print("This script can only be run on macOS.")
        return []
    
    applescript = f'''
    tell application "Notes"
        set theNote to the first note whose name is "{note_title}"
        set noteContent to body of theNote
    end tell
    return noteContent
    '''
    process = subprocess.run(['osascript', '-e', applescript], capture_output=True, text=True)
    return process.stdout.strip()

def write_note_to_file(note_content, filename="data.txt"):
    """Writes note content to a file, overwriting existing content."""
    with open(filename, 'w') as file:
        file.write(note_content.replace("<div>", "").replace("</div>", ""))

# Retrieve note content
note_title = "THE ARC"  # Replace with your note's title
note_content = get_note_content(note_title)

# Check if note content is not empty before writing to file
if note_content != [] and note_content:
    write_note_to_file(note_content)
else:
    print(f"Note titled '{note_title}' does not exist or is empty.")

# Read data from the updated file
filename = "data.txt"
data = read_data_from_file(filename)

# Parse data
dates = []
weights = []
distances = {}
activities = []
year = None

maxWeight = 0
minWeight = 1000000
currentWeight = 0
nbrOfHoles = 0

for item in data:
    if item[0] == "Y":
        year = item[1:]
    else:
        print(item)
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
        
        if weightOrDistance is None:
            weightOrDistance = weights[-1]
        elif activity == 'golf':
            nbrOfHoles += int(weightOrDistance)
            weightOrDistance = weights[-1]
        elif activity in ['run', 'löpning', 'gång', 'walk', 'cykel', 'bike', 'promenad', 'walk', 'vandring', 'hiking']:
            distances[len(activities)] = float(weightOrDistance[:-2])
            weightOrDistance = weights[-1]
        else:
            weightOrDistance = float(weightOrDistance[:-2])
            maxWeight = max(maxWeight, weightOrDistance)
            minWeight = min(minWeight, weightOrDistance)
            currentWeight = weightOrDistance
        
        full_date = f"{day}/{month}/{year}"
        dates.append(full_date)
        weights.append(weightOrDistance)
        activities.append(activity)

# Convert date strings to datetime objects
dates = [datetime.strptime(date, '%d/%m/%Y') for date in dates]
min_date = min(dates)
max_date = max(dates)
span_days = max((max_date - min_date).days, 1)
pad_days = max(3, int(span_days * 0.02))
pad_delta = timedelta(days=pad_days)
x_axis_min = min_date - pad_delta
x_axis_max = max_date + pad_delta

# Plot data
fig = plt.figure(figsize=(10, 6))
gs = fig.add_gridspec(
    1,
    2,
    width_ratios=[4, 1],
    left=0.08,
    right=0.97,
    bottom=0.25,
    top=0.95,
    wspace=0.05,
)
ax = fig.add_subplot(gs[0, 0])
legend_ax = fig.add_subplot(gs[0, 1])
legend_ax.set_facecolor('white')
legend_ax.set_xticks([])
legend_ax.set_yticks([])
legend_ax.set_xlim(0, 1)
legend_ax.set_ylim(0, 1)
for spine in legend_ax.spines.values():
    spine.set_visible(True)
ax.set_xlim(x_axis_min, x_axis_max)

# Create a color map for activities
activity_colors = {activity: f"C{i}" for i, activity in enumerate(set(activities))}

# Add a line plot to connect the points
ax.plot(dates, weights, linestyle='-', color='red', alpha=0.5)

# Plot each point with the corresponding activity color
ax.scatter(dates, weights, c=[activity_colors[activity] for activity in activities])

# Prepare annotation that follows the mouse based on closest weight
annotation = ax.annotate(
    "",
    xy=(0, 0),
    xytext=(15, -30),
    textcoords="offset points",
    bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="black", lw=0.5),
    arrowprops=dict(arrowstyle="->"),
)
annotation.set_visible(False)

def format_annotation_text(index):
    base_text = [
        f"Date: {dates[index].strftime('%Y-%m-%d')}",
        f"Activity: {activities[index]}",
        f"Weight: {weights[index]} kg",
    ]
    if activities[index] in ['löpning', 'run'] and index in distances:
        base_text.append(f"Distance: {distances[index]} km")
    return "\n".join(base_text)

def on_mouse_move(event):
    if event.inaxes != ax or event.ydata is None:
        if annotation.get_visible():
            annotation.set_visible(False)
            fig.canvas.draw_idle()
        return
    target_y = event.ydata
    closest_index = min(range(len(weights)), key=lambda i: abs(weights[i] - target_y))
    annotation.xy = (dates[closest_index], weights[closest_index])
    annotation.set_text(format_annotation_text(closest_index))
    if not annotation.get_visible():
        annotation.set_visible(True)
    fig.canvas.draw_idle()

fig.canvas.mpl_connect("motion_notify_event", on_mouse_move)

# Calculate the number of activities, number of days, and total kilometers
num_activities = len(activities)
start_date = min_date
num_days = (max_date - start_date).days
total_kilometers = sum(distances.values())

# Add legend for activities with additional summary information
activity_counts = Counter(activities)
legend_labels = [f"{activity} ({count})" for activity, count in activity_counts.items()]
summary_label = f"Consistency: {num_activities}/{num_days} days\nTotal km: {total_kilometers:.2f}\nMax weight: {maxWeight}kg\nMin weight: {minWeight}kg\nCurrent weight: {currentWeight}kg"

legend_ax.legend(
    handles=[
        plt.Line2D([0], [0], marker='o', color='w', label=label,
                   markerfacecolor=activity_colors[activity], markersize=10)
        for activity, label in zip(activity_counts.keys(), legend_labels)
    ] + [plt.Line2D([0], [0], color='w', label=summary_label)],
    loc='upper left',
    frameon=False,
    handletextpad=0.5
)

# Set labels and title
ax.set_xlabel('Date')
ax.set_ylabel('Weight (kg)')

# Set y-axis limits slightly beyond observed weights
ax.set_ylim(min(weights) - 1, max(weights) + 1)

ax.set_title('Weight Over Time with Activities')

# Configure x-axis ticks to show the first day of each month starting after the first activity
def first_day_of_next_month(date_obj):
    if date_obj.month == 12:
        return datetime(date_obj.year + 1, 1, 1)
    return datetime(date_obj.year, date_obj.month + 1, 1)

month_tick = first_day_of_next_month(min_date)
last_date = max_date
month_ticks = []
while month_tick <= last_date:
    month_ticks.append(month_tick)
    if month_tick.month == 12:
        month_tick = datetime(month_tick.year + 1, 1, 1)
    else:
        month_tick = datetime(month_tick.year, month_tick.month + 1, 1)

if not month_ticks:
    month_ticks = [month_tick]

if month_ticks:
    tick_labels = [tick.strftime('%b %Y') for tick in month_ticks]
    ax.set_xticks(month_ticks)
    ax.set_xticklabels(tick_labels, rotation=45, ha='right')

# Add a horizontal range slider to zoom the x-axis
ax_pos = ax.get_position()
slider_ax = fig.add_axes([ax_pos.x0, 0.08, ax_pos.width, 0.03])
padded_start_num = mdates.date2num(x_axis_min)
padded_end_num = mdates.date2num(x_axis_max)
date_slider = RangeSlider(
    ax=slider_ax,
    label='Date Range',
    valmin=padded_start_num,
    valmax=padded_end_num,
    valinit=(padded_start_num, padded_end_num),
)

def update_range(_):
    start_num, end_num = date_slider.val
    ax.set_xlim(mdates.num2date(start_num), mdates.num2date(end_num))
    date_slider.valtext.set_text(
        f"{mdates.num2date(start_num).strftime('%b %Y')} - {mdates.num2date(end_num).strftime('%b %Y')}"
    )
    fig.canvas.draw_idle()

date_slider.on_changed(update_range)
update_range(None)

# Show plot
plt.get_current_fig_manager().resize(2700, 1600)
plt.show()
