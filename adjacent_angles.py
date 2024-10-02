import numpy as np
import quaternion
from datetime import datetime
import os

def quaternion_from_line(line):
    if line.startswith('#') or not line.strip():
        return None, None  # Skip empty lines and lines starting with '#'

    parts = line.strip().split(' ')
    if len(parts) < 3:
        return None, None  # Skip lines that don't have enough parts

    date_str, time_str, quaternion_str = parts[0], parts[1], parts[2]

    try:
        # Combine date and time strings and convert to datetime
        timestamp_str = f"{date_str} {time_str}"
        timestamp = datetime.strptime(timestamp_str, "%m/%d/%y %H:%M:%S.%f")

        # Convert quaternion components to float
        q_components = [float(x) for x in quaternion_str.split(',')]

        # Create quaternion with w, x, y, z order
        q = quaternion.quaternion(q_components[3], q_components[0], q_components[1], q_components[2])

        return timestamp, q
    except ValueError:
        return None, None  # Skip lines that cannot be parsed as timestamps or quaternions

# Function to read sensor data from multiple files in a directory
def read_sensor_data(directory):
    sensor_quaternions = {}
    for root, dirs, files in os.walk(directory):
        for file_name in files:
            file_path = os.path.join(root, file_name)
            with open(file_path, 'r') as file:
                for line in file:
                    timestamp, q = quaternion_from_line(line)
                    if timestamp is not None:
                        sensor_quaternions[timestamp] = q
    return sensor_quaternions

# Function to calculate angles between sensors
def calculate_angles(sensor1_quaternions, sensor2_quaternions, sensor3_quaternions):
    # Get common timestamps
    common_timestamps = sorted(set(sensor1_quaternions.keys()) & set(sensor2_quaternions.keys()) & set(sensor3_quaternions.keys()))

    # Initialize lists to store angles
    flexion_angles = []
    extension_angles = []
    lateral_flexion_angles = []
    rotation_angles = []

    for timestamp in common_timestamps:
        q1 = sensor1_quaternions[timestamp]
        q2 = sensor2_quaternions[timestamp]
        q3 = sensor3_quaternions[timestamp]

        # Calculate relative Euler angles between sensors (1, 2) and (2, 3)
        euler_angles_12 = quaternion_to_euler(q2 * q1.inverse())
        euler_angles_23 = quaternion_to_euler(q3 * q2.inverse())

        # Append Euler angles to lists
        flexion_angles.append((euler_angles_12[0], euler_angles_23[0]))
        extension_angles.append((-euler_angles_12[0], -euler_angles_23[0]))
        lateral_flexion_angles.append((euler_angles_12[1], euler_angles_23[1]))
        rotation_angles.append((euler_angles_12[2], euler_angles_23[2]))

    return common_timestamps, flexion_angles, extension_angles, lateral_flexion_angles, rotation_angles

# Function to convert quaternion to Euler angles
def quaternion_to_euler(q):
    roll = np.arctan2(2 * (q.y * q.z + q.x * q.w), 1 - 2 * (q.x**2 + q.y**2))
    pitch = np.arcsin(2 * (q.x * q.z - q.y * q.w))
    yaw = np.arctan2(2 * (q.x * q.y + q.z * q.w), 1 - 2 * (q.y**2 + q.z**2))
    return np.degrees(np.array([roll, pitch, yaw]))

# Prompt the user for the parent directory containing sensor data folders
parent_directory = input("Enter the parent directory path containing sensor data folders: ")

# Prompt the user for the names of the sensor data folders
sensor_directories = [input(f"Enter the name of sensor data folder {i+1}: ") for i in range(3)]

try:
    # Read sensor data from files in each directory
    sensor_quaternions = [read_sensor_data(os.path.join(parent_directory, directory)) for directory in sensor_directories]

    # Calculate angles between sensors (1, 2) and (2, 3)
    common_timestamps, flexion_angles, extension_angles, lateral_flexion_angles, rotation_angles = calculate_angles(*sensor_quaternions)

    # Print and save results to a new text file
    output_file_path = 'output_angles_between_sensors.txt'

    with open(output_file_path, 'w') as output_file:
        output_file.write("Timestamp\t\t\tFlexion (1-2)\tFlexion (2-3)\tExtension (1-2)\tExtension (2-3)\tLateral Flexion (1-2)\tLateral Flexion (2-3)\tRotation (1-2)\tRotation (2-3)\n")
        for i, timestamp in enumerate(common_timestamps):
            flexion_12, flexion_23 = flexion_angles[i]
            extension_12, extension_23 = extension_angles[i]
            lateral_flexion_12, lateral_flexion_23 = lateral_flexion_angles[i]
            rotation_12, rotation_23 = rotation_angles[i]

            output_file.write(f"{timestamp}\t{flexion_12}\t{flexion_23}\t{extension_12}\t{extension_23}\t{lateral_flexion_12}\t{lateral_flexion_23}\t{rotation_12}\t{rotation_23}\n")

    print(f"Angles between sensors saved to {output_file_path}")

except FileNotFoundError:
    print("File not found. Please check the directory paths and try again.")
except Exception as e:
    print(f"An error occurred: {e}")
