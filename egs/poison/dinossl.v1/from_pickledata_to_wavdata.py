import sys
import pickle
import os
from tqdm import tqdm
import scipy.io.wavfile

dataset_path, fs = sys.argv[1], sys.argv[2]

output = "/export/b17/tthebau1/GARD_data"
if not os.path.exists(output): os.mkdir(output)
os.system(f"rm -r {output}/*" )
os.system(f"cp {dataset_path}/poison_index_train {output}/")

with open(f"{dataset_path}/y_poison_train",'rb') as file:
    labels = pickle.load(file)
print(f"Labels loaded :{labels.shape}")
with open(f"{dataset_path}/x_poison_train",'rb') as file:
    dataset = pickle.load(file)
print(f"Data loaded :{dataset.shape}")

for idx, (label, data) in tqdm(enumerate(zip(labels, dataset)), total=len(labels)):
    out_dir = os.path.join(output,str(label))
    if not os.path.exists(out_dir): os.mkdir(out_dir)
    scipy.io.wavfile.write(f"{out_dir}/{idx}.wav", int(fs), data)

print(f"Data saved")
