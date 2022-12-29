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
./prepare_egs_paths.sh
```
This script will ask for the path to your anaconda installation and enviromentment name.
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

## Training of a DINO SSL network on poisoned data
### Setup paths and datasets
To train DINO, you will need the RIRS and MUSAN noises datasets, 
If you want to do without them, just ... TODO
RIRS will be downloaded automatically, not MUSAN.
You can download it at TODO, then put the path to musan in the env variable musan_path

```bash
export musan_path= path/to/musan #replace this by the path to musan dataset
export poison_path= path/to/poisoned_dataset #replace this by the path to the poisoned dataset extracted
export poison_name=scenario1 #replace this by the name you wish to give at this experiment, if you want to run multiple in the same docker.
```

### 
