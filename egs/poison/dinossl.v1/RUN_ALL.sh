#!/bin/bash
# Copyright
#                2023   Johns Hopkins University (Author: Thomas Thebaud)
# Apache 2.0.
#

# Arguments : poison_path, poison_name, musan_path, -t

export poison_path=/workspace/dump_dir #replace this by the path to the poisoned dataset extracted

export poison_name=scenario1 

export musan_path=/workspace/musan #replace this by the path to musan dataset


if [ ! -d "/workspace/new_dump" ]; then mkdir /workspace/new_dump; fi
python from_pickledata_to_wavdata.py $poison_path 16000 "/workspace/new_dump"
export poison_path=/workspace/new_dump

echo "### Preparing the dataset ###"
bash run_001_prepare_data.sh
echo "### Computing VAD ###"
bash run_002_compute_evad.sh
if [ "$1" = "retrain" ];
    then 
        echo "##--## Preparing to train a new model ##--##"
        echo "### Preparing the noise datasets ###"
        bash run_003_prepare_noises_rirs.sh
        echo "### Preparing the training data ###"
        bash run_010_prepare_xvec_train_data.sh
        echo "## TRAINING DINO ##"
        bash run_511_train_xvector.sh
        echo "Training finished"
    else 
        echo "Using pre trained model"
fi

echo "### Extracting xvectors ###"
bash run_030_extract_xvectors.sh
echo "### Running Clustering s###"
python clustering.py 1000 -1 "exp/xvectors/fbank80_stmn_lresnet34_e256_do0_b48_amp.dinossl.v1/${poison_name}" ${poison_name}
echo "List extracted"