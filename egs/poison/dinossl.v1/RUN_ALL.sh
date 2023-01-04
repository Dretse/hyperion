#!/bin/bash
# Copyright
#                2023   Johns Hopkins University (Author: Thomas Thebaud)
# Apache 2.0.
#

# Arguments : poison_path, poison_name, musan_path, -t

if [ -z ${1+x} ];
    then export poison_path=/export/b17/xli257/poison; #replace this by the path to the poisoned dataset extracted
    else export poison_path=$1; 
fi

if [ -z ${2+x} ];
    then export poison_name=poison_full; 
    else export poison_name=$2; 
fi

if [ -z ${3+x} ];
    then export musan_path=/export/corpora5/JHU/musan; #replace this by the path to musan dataset
    else export musan_path=$3; 
fi

#python from_pickledata_to_wavdata.py $poison_full_root 16000 "/export/b17/tthebau1/GARD_data"
#export poison_path=/export/b17/tthebau1/GARD_data

echo "Preparing the dataset"
bash run_001_prepare_data.sh
echo "Computing VAD"
bash run_002_compute_evad.sh
if [ -z ${4+x} ];
    then 
        echo "Preparing to train a new model"
        echo "Preparing the noise datasets"
        bash run_003_prepare_noises_rirs.sh
        echo "Preparing the training data"
        bash run_010_prepare_xvec_train_data.sh
        echo "TRAINING DINO"
        bash run_511_train_xvector.sh
        echo "Training finished"
    else 
        echo "Using pre trained model"
fi

echo "Extracting xvectors"
bash run_030_extract_xvectors.sh
echo "Running Clustering"
python clustering.py 1000 -1 "exp/xvectors/fbank80_stmn_lresnet34_e256_do0_b48_amp.dinossl.v1/${poison_name}" ${poison_name}
echo "List extracted"