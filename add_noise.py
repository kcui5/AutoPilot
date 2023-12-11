import numpy as np

file_name = ".txt"
lines = []
with open(file_name, 'r') as f:
    for line in f:
        time, x, y = line.split(',')
        lines.append(f"{time},{x+np.random.normal(loc=0, scale=7)},{y+np.random.normal(loc=0, scale=7)}")

for i in range(10):
    new_file_name = file_name[:-4] + i + ".txt"
    with open(new_file_name, 'w') as f:
        for line in lines:
            f.write(line + "\n")
