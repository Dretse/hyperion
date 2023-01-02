# HYPERION 4 ARMORY

## Setup of the the environment

### Clone Hyperion from my branch
```bash
git clone https://github.com/Dretse/hyperion.git
```

### Create conda env and install hyperion
```bash
cd hyperion
conda env create --name ${your_env} -f environment.yml
conda activate ${your_env}
pip install kaldiio
pip install -e .
```

After installation, add these lines to your `~/.bashrc`
```bash
HYP_ROOT= #substitute this by your hyperion location
export PYTHONPATH=${HYP_ROOT}:$PYTHONPATH
export PATH=${HYP_ROOT}/bin:$PATH
```

Finally configure the python and environment name that you intend to use to run the recipes.
For that run
```bash
source ~/.bashrc
conda activate ${your_env}
./prepare_egs_paths.sh
```
This script will ask for the path to your anaconda installation and environment name.
(you can use 'which python' command to find where its stored).
It will also detect if hyperion is already installed in the environment,
otherwise it will add hyperion to your python path.
This will create the file
```
tools/path.sh
```
which sets all the enviroment variables required to run the recipes.
This has been tested only on JHU computer grids, so you may need to 
modify this file manually to adapt it to your grid.


## Training of a new DINO SSL network on poisoned data
### Setup paths and datasets
To train DINO, you will need the RIRS and MUSAN noises datasets, 
If you want to do without them, just ... TODO
RIRS will be downloaded automatically, not MUSAN.
You can download it at https://us.openslr.org/resources/17/musan.tar.gz , then put the path to musan in the env variable musan_path

```bash
export musan_path= path/to/musan #replace this by the path to musan dataset
export poison_path= path/to/poisoned_dataset #replace this by the path to the poisoned dataset extracted
export poison_name=scenario1 #replace this by the name you wish to give to this experiment, if you want to run multiple in the same docker.
```

### Training the system
launch every command file in the list, in the right order.
To get more informations about what each of them does, go read the README.md file.
```bash
cd egs/poison/dinossl.v1/ 
run_001_prepare_data.sh
run_002_compute_evad.sh
run_003_prepare_noises_rirs.sh
run_010_prepare_xvec_train_data.sh
run_511_train_xvector.sh
run_030_extract_xvectors.sh
```
At the end, a set of unsupervised representations is generated, that will be used to determine which one are poisoned and which one are not.
The trained dino can be found in exp/xvector_nnets/fbank80_stmn_lresnet34_e256_do0_b48_amp.dinossl.v1/
The extracted representations can be found in exp/xvectors/fbank80_stmn_lresnet34_e256_do0_b48_amp.dinossl.v1/${poison_name}/

### Production of the list of utterances to keep
you can generate a pickeled list of the indicies to keep for later under the name of poison_name.pkl using the command :
```
python clustering.py 1000 -1 "exp/xvectors/fbank80_stmn_lresnet34_e256_do0_b48_amp.dinossl.v1/${poison_name}" ${poison_name}
```
1000 is the number of clusters used

-1 is for removing every detected poisoned example. 
In a situation where the defender knows only N classes were used to attack, 
you can change this parameter by N (int) to only remove the N classes with the more examples detected as poisoned,
and drastrically lower the amount of false positives examples.

The third parameter is the directory where the representations extracted are stored.

The last parameter will be used to save the indices of the files to keep/remove.
This script generate two files at the root of hyperion : 
${poison_name}.pkl and ${poison_name}_LDA.pkl, 
the second is gives slightly better results using an LDA based on the results of the first one.


## Using a trained system
If you already have the noises prepared and a trained model,
exp/xvector_nnets/fbank80_stmn_lresnet34_e256_do0_b48_amp.dinossl.v1/model_ep0070.pth, can be found here : 
https://drive.google.com/file/d/1KMnknps7PsjuBZ3GPcDdiSHTWN_l8fFQ/view?usp=sharing
you can use it directly on a new dataset by doing the following operations:

### Changing the env variables

```bash
export poison_path= path/to/new/poisoned_dataset #replace this by the path to the new poisoned dataset extracted
export poison_name=scenario2 #replace this by the name you wish to give to this experiment.
```

### Extracting the new vectors
```bash
run_001_prepare_data.sh 
run_002_compute_evad.sh 
run_030_extract_xvectors.sh
```

### And extracting the new pkl list
```
python clustering.py 1000 -1 "exp/xvectors/fbank80_stmn_lresnet34_e256_do0_b48_amp.dinossl.v1/${poison_name}" ${poison_name}
```

