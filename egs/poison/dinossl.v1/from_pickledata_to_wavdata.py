import sys
import pickle
import os
from tqdm import tqdm
import scipy.io.wavfile
import numpy as np

dataset_path, fs, output = sys.argv[1], sys.argv[2], sys.argv[3]

if not os.path.exists(output): 
    os.system(f"mkdir -p {output}")
else:
    os.system(f"rm -r {output}/*" )

if len(sys.argv)==4:
    print("Moving train set")
    with open(f"{dataset_path}/y_poison_train",'rb') as file:
        labels = pickle.load(file)
    print(f"Labels loaded :{labels.shape}")
    with open(f"{dataset_path}/x_poison_train",'rb') as file:
        dataset = pickle.load(file)
    print(f"Data loaded :{dataset.shape}")
else:
    print("Moving test set")
    root = f"{dataset_path}/test/"
    dataset, labels = [], []
    for filename in tqdm(os.listdir(root)):
        with open(root+filename,'rb') as file:
            data = pickle.load(file)
        if 'x' in filename:
            if len(dataset)==0: dataset=data
            else: dataset = np.concatenate((dataset, data))
        elif 'y_adv' in filename:
            if len(labels)==0: labels=data
            else: labels = np.concatenate((labels, data))
    print(f"Data loaded :{dataset.shape}")


for idx, (label, data) in tqdm(enumerate(zip(labels, dataset)), total=len(labels)):
    if isinstance(label, np.ndarray): out_dir = os.path.join(output,str(np.argmax(label)))
    else: out_dir = os.path.join(output,str(label))

    if not os.path.exists(out_dir): os.mkdir(out_dir)
    scipy.io.wavfile.write(f"{out_dir}/{idx}.wav", int(fs), data)

print(f"Data saved")
