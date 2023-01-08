import pandas as pd
import sys
import numpy as np

input_file, output_file, parameters = sys.argv[1], sys.argv[2], sys.argv[3]

with open(input_file, 'r') as file:
    lines = file.readlines()

if parameters=='{print $1}':
    output_lines = [line.split(' ')[0]+'\n' for line in lines]
elif parameters=='{ if (NF == 2 && $2 > 0) { print }}':
    output_lines = [line+'\n' for line in lines if(len(line.strip('\n').split(' '))==2 and float(line.split(' ')[1])>0)]
elif parameters=='/status 0/ { print 0} !/status 0/ { print 1}':
    print(np.sum([1 if 'status 0' in line else 0 for line in lines]))
    exit()
else:
    print(f'Parameter {parameters} not programed yet. please add option in awk.py')
    exit(1)

with open(output_file, 'w') as file:
    file.writelines(lines)