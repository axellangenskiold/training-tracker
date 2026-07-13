import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from collections import Counter
from datetime import datetime, timedelta
import subprocess
import platform
import re
from matplotlib.widgets import RangeSlider


def extract_number(text):
    """Pull the first number out of e.g. '78kg', '6 km', '14.2km'."""
    match = re.search(r'-?\d+(?:\.\d+)?', text)
    if match is None:
        raise ValueError(f"no number in {text.strip()!r}")
    return float(match.group())


def rolling_average(sample_dates, values, window_days=7):
    """Centered time-window average, smoothing day-to-day weigh-in noise."""
    # ponytail: O(n^2) over weigh-ins, fine for a few hundred points
    half = window_days / 2
    return [
        sum(v for d2, v in zip(sample_dates, values) if abs((d2 - d).days) <= half)
        / sum(1 for d2 in sample_dates if abs((d2 - d).days) <= half)
        for d in sample_dates
    ]

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
holes = {}
activities = []
is_weighin = []
year = None

maxWeight = 0
minWeight = 1000000
currentWeight = 0
nbrOfHoles = 0

activities_dict = [
    'run', 
    'löpning', 
    'gång', 
    'walk', 
    'cykel', 
    'bike', 
    'promenad', 
    'vandring', 
    'hiking', 
    'hike',
    'mountainbike',
    'via ferrata'
    ]

last_weight = None
for line_no, item in enumerate(data, start=2):  # data[] starts at file line 2
    if not item:
        continue
    if item[0] == "Y":
        year = item[1:]
        continue
    try:
        date, rest = item.split(":", 1)
        day, month = date.strip().split("/")

        rest_parts = rest.split(",")
        activity = rest_parts[0].strip()
        value = rest_parts[1].strip() if len(rest_parts) > 1 else None

        weighed = False
        if value is None:
            weight = last_weight
        elif activity == 'golf':
            holes[len(activities)] = int(extract_number(value))
            nbrOfHoles += holes[len(activities)]
            weight = last_weight
        elif activity in activities_dict:
            distances[len(activities)] = extract_number(value)
            weight = last_weight
        else:
            weight = extract_number(value)
            last_weight = weight
            maxWeight = max(maxWeight, weight)
            minWeight = min(minWeight, weight)
            currentWeight = weight
            weighed = True

        dates.append(f"{day.strip()}/{month.strip()}/{year}")
        weights.append(weight)  # may be None until the first weigh-in
        activities.append(activity)
        is_weighin.append(weighed)
    except (ValueError, IndexError) as error:
        print(f"Skipping malformed line {line_no}: {item!r} ({error})")

# Backfill any activity days logged before the first weigh-in
first_known = next((w for w in weights if w is not None), None)
if first_known is None:
    raise SystemExit("No weight entries found — nothing to plot.")
weights = [first_known if w is None else w for w in weights]

# Convert date strings to datetime objects
dates = [datetime.strptime(date, '%d/%m/%Y') for date in dates]
date_numbers = mdates.date2num(dates)
min_date = min(dates)
max_date = max(dates)
span_days = max((max_date - min_date).days, 1)
pad_days = max(3, int(span_days * 0.02))
pad_delta = timedelta(days=pad_days)
x_axis_min = min_date - pad_delta
x_axis_max = max_date + pad_delta

# Modern, clean theme
INK = '#16181d'       # near-black for text / trend line
MUTED = '#8a909c'     # ticks and secondary text
plt.rcParams.update({
    'figure.facecolor': '#f4f5f7',
    'axes.facecolor': '#ffffff',
    'axes.edgecolor': '#d9dce1',
    'axes.linewidth': 1.0,
    'axes.axisbelow': True,
    'axes.labelcolor': MUTED,
    'text.color': '#3a3f4a',
    'xtick.color': MUTED,
    'ytick.color': MUTED,
    'xtick.labelsize': 9,
    'ytick.labelsize': 9,
    'font.size': 10,
})

# Plot data
fig = plt.figure(figsize=(12, 6.5))
gs = fig.add_gridspec(
    1,
    2,
    width_ratios=[4, 1.35],
    left=0.06,
    right=0.985,
    bottom=0.24,
    top=0.90,
    wspace=0.04,
)
ax = fig.add_subplot(gs[0, 0])
ax.spines[['top', 'right']].set_visible(False)
ax.grid(axis='y', color='#e9ebef', linewidth=1.0)
ax.tick_params(length=0)
legend_ax = fig.add_subplot(gs[0, 1])
legend_ax.set_facecolor('#ffffff')
legend_ax.set_xticks([])
legend_ax.set_yticks([])
legend_ax.set_xlim(0, 1)
legend_ax.set_ylim(0, 1)
for spine in legend_ax.spines.values():
    spine.set_visible(False)
ax.set_xlim(x_axis_min, x_axis_max)

# Distinct color per activity (tab20 gives 20 unambiguous hues), stable across runs
palette = plt.cm.tab20.colors
activity_colors = {a: palette[i % len(palette)] for i, a in enumerate(sorted(set(activities)))}

# Faint line connecting the raw points, so the coloured dots stay the focus
ax.plot(dates, weights, linestyle='-', color='#c9cdd4', linewidth=1.0, zorder=1)

# Plot each point with the corresponding activity color
ax.scatter(dates, weights, c=[activity_colors[activity] for activity in activities],
           s=30, edgecolor='white', linewidth=0.6, zorder=3)

# Overlay a 7-day rolling average of weigh-ins to show the bodyweight trend
weighin_dates = [d for d, w in zip(dates, is_weighin) if w]
weighin_weights = [wt for wt, w in zip(weights, is_weighin) if w]
if len(weighin_dates) >= 2:
    trend = rolling_average(weighin_dates, weighin_weights, window_days=7)
    # Break the line across long gaps (>21 days) instead of drawing a fake diagonal
    seg_x, seg_y, prev = [], [], None
    for d, t in zip(weighin_dates, trend):
        if prev is not None and (d - prev).days > 21:
            seg_x.append(prev)
            seg_y.append(float('nan'))
        seg_x.append(d)
        seg_y.append(t)
        prev = d
    ax.plot(seg_x, seg_y, color=INK, linewidth=2.2, zorder=4,
            solid_capstyle='round', label='7-day weight trend')

# Prepare annotation that follows the mouse based on closest weight
annotation = ax.annotate(
    "",
    xy=(0, 0),
    xytext=(15, -30),
    textcoords="offset points",
    bbox=dict(boxstyle="round,pad=0.5", fc=INK, ec="none"),
    arrowprops=dict(arrowstyle="->", color=INK),
    color="white",
    fontsize=9,
    zorder=6,
)
annotation.set_visible(False)

def format_annotation_text(index):
    base_text = [
        f"Date: {dates[index].strftime('%Y-%m-%d')}",
        f"Activity: {activities[index]}",
        f"Weight: {weights[index]} kg",
    ]
    if index in distances:
        base_text.append(f"Distance: {distances[index]} km")
    if index in holes:
        base_text.append(f"Holes: {holes[index]}")
    return "\n".join(base_text)

def on_mouse_move(event):
    if event.inaxes != ax or event.xdata is None:
        if annotation.get_visible():
            annotation.set_visible(False)
            fig.canvas.draw_idle()
        return
    target_x = event.xdata
    closest_index = min(
        range(len(date_numbers)),
        key=lambda i: abs(date_numbers[i] - target_x)
    )
    current_xlim = ax.get_xlim()
    margin = (current_xlim[1] - current_xlim[0]) * 0.15
    if date_numbers[closest_index] > current_xlim[1] - margin:
        annotation.xytext = (-15, -30)
        annotation.set_ha('right')
    else:
        annotation.xytext = (15, -30)
        annotation.set_ha('left')
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

# Right panel: activity legend on top, summary stats in a card below
activity_counts = Counter(activities)
legend_handles = [
    plt.Line2D([0], [0], marker='o', linestyle='none', label=f"{activity} ({count})",
               markerfacecolor=activity_colors[activity], markeredgecolor='white',
               markersize=8)
    for activity, count in activity_counts.items()
]
legend_handles.append(
    plt.Line2D([0], [0], color=INK, linewidth=2.2, label='7-day weight trend')
)
legend_ax.legend(
    handles=legend_handles,
    loc='upper left',
    bbox_to_anchor=(0.0, 1.0),
    frameon=False,
    handletextpad=0.6,
    labelspacing=0.45,
    fontsize=8.5,
)

summary_text = "\n".join([
    f"Consistency   {num_activities}/{num_days} days",
    f"Total km      {total_kilometers:.0f}",
    f"Golf holes    {nbrOfHoles}",
    f"Weight now    {currentWeight} kg",
    f"Min / Max     {minWeight} / {maxWeight} kg",
])
legend_ax.text(
    0.0, 0.0, summary_text,
    transform=legend_ax.transAxes,
    va='bottom', ha='left',
    family='monospace', fontsize=8.5, color='#3a3f4a', linespacing=1.6,
    bbox=dict(boxstyle='round,pad=0.6', fc='#f4f5f7', ec='#e2e5ea'),
)

# Set labels and title
ax.set_ylabel('Weight (kg)')

# Set y-axis limits slightly beyond observed weights
ax.set_ylim(min(weights) - 1, max(weights) + 1)

ax.set_title('Weight over time with activities', loc='left', fontsize=15,
             fontweight='bold', color=INK, pad=14)

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
slider_ax.set_facecolor('#e9ebef')
date_slider = RangeSlider(
    ax=slider_ax,
    label='',
    valmin=padded_start_num,
    valmax=padded_end_num,
    valinit=(padded_start_num, padded_end_num),
    color=INK,
)
date_slider.valtext.set_color(MUTED)
date_slider.valtext.set_fontsize(9)

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
