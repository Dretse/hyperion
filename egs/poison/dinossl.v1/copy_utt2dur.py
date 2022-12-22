import sys

input_file, output_file = sys.argv[2], sys.argv[1]
with open(input_file+'/utt2dur', 'r') as file:
    lines = file.readlines()

lines = [line.split(' ')[0]+' 1.0\n' for line in lines]

with open(output_file+'/utt2dur', 'w') as file:
    file.writelines(lines)