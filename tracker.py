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

