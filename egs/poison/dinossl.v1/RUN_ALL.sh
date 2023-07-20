#!/bin/bash
# Copyright
#                2023   Johns Hopkins University (Author: Thomas Thebaud)
# Apache 2.0.
#

# Arguments : poison_path, poison_name, musan_path, -t

convertsecs() {
 ((h=${1}/3600))
 ((m=(${1}%3600)/60))
 ((s=${1}%60))
 printf "%02d:%02d:%02d\n" $h $m $s
}

if [ -z ${1+x} ]; then poison_name=scenario1; else poison_name=$1; fi
if [ -z ${2+x} ]; then stage=1; else stage=$2; fi #[optional, default=1] stage to start from.
if [ -z ${3+x} ]; then n_gpu=1; else n_gpu=$3; fi #[optional, default=1] number of GPU to use. tested from 1 to 4GPU
if [ -z ${4+x} ]; then class_attacked=1; else class_attacked=$4; fi #[optional, default=1] how many classes are you expected to get attacked.
# The number of class attacked should be kept as 1. it will generate anyway a list with all the classes removed, and one with only one class removed.
# If you want to always keep everything, you can put this value at -1

export poison_path=/workspace/dump_dir #replace this by the path to the poisoned dataset extracted
export new_poison_path=/workspace/new_dump #fixed
export musan_path=/workspace/musan #replace this by the path to musan dataset

if [ ! -d $new_poison_path ]; then mkdir $new_poison_path; fi

echo "Starting at stage $stage. Training (stage 6) will be done with $n_gpu gpus. Hypothesis: $class_attacked classes attacked"
echo "Using the threat model $poison_name"

#export poison_path="/export/b17/xli257/poison_data_dumps/${poison_name}" #replace this by the path to the poisoned dataset extracted
#export musan_path=/export/corpora5/JHU/musan
#export new_poison_path=/export/b17/tthebau1/temp/$poison_name
 
if [ $stage -le 1 ];then 
    echo "Starting stage 1"
    start=`date +%s`
    python from_pickledata_to_wavdata.py $poison_path 16000 $new_poison_path || exit 1;
    end=`date +%s`
    time_taken=`expr $end - $start`
    echo "End of stage 1, Execution time was $time_taken seconds." #time measured: 3:31
fi

export poison_path=$new_poison_path

if [ $stage -le 2 ];then 
    echo "### Preparing the dataset, stage 2 ###"
    start=`date +%s`
    bash run_001_prepare_data.sh || exit 1;
    end=`date +%s`
    time_taken=`expr $end - $start`
    echo "End of stage 2, Execution time was $time_taken seconds." #time measured 1sec

fi

if [ $stage -le 3 ];then
    echo "### Computing VAD, stage 3 ###" 
    start=`date +%s`
    bash run_002_compute_evad.sh || exit 1;
    end=`date +%s`
    time_taken=`expr $end - $start`
    echo "End of stage 3, Execution time was $time_taken seconds." #time measured 5:17

fi

if [ $stage -le 4 ];then 
    echo "### Preparing the noise datasets, stage 4 ###"
    start=`date +%s`
    bash run_003_prepare_noises_rirs.sh || exit 1;
    end=`date +%s`
    time_taken=`expr $end - $start`
    echo "End of stage 4, Execution time was $time_taken seconds." #time measured 20:42

fi

if [ $stage -le 5 ];then 
    echo "### Preparing the training data, stage 5 ###"
    start=`date +%s`
    bash run_010_prepare_xvec_train_data.sh || exit 1;
    end=`date +%s`
    time_taken=`expr $end - $start`
    echo "End of stage 5, Execution time was $time_taken seconds." #time measured 44:42

fi

if [ $stage -le 6 ];then
    echo "## TRAINING DINO ##"
    start=`date +%s`
    if [ $n_gpu -ge 2 ];then
        echo "Using multiple gpus"
        bash run_511_train_xvector_multi_gpu.sh $n_gpu || exit 1;
    else
        bash run_511_train_xvector.sh || exit 1;
    fi
    end=`date +%s`
    time_taken=`expr $end - $start`
    echo "Training finished, Execution time was $time_taken seconds." #time measured: 25h on 1GPU, 15h on 2GPU, 6h on 4GPU

fi

if [ $stage -le 7 ];then
    echo "### Extracting xvectors ### stage 7"
    start=`date +%s`
    bash run_030_extract_xvectors.sh || exit 1;
    end=`date +%s`
    time_taken=`expr $end - $start`
    echo "End of stage 7, Execution time was $time_taken seconds."
fi

if [ $stage -le 8 ];then 
    echo "echo ### Running Clustering ###, stage 8"
    if [ $class_attacked -le 0 ];then 
        echo "Unknown number of classes attacked."
    else
        echo "hyp: $class_attacked classes attacked."
    fi

    start=`date +%s`
    python clustering.py 1000 $class_attacked "exp/xvectors/fbank80_stmn_lresnet34_e256_do0_b48_amp.dinossl.v1/${poison_name}" ${poison_name} || exit 1;
    end=`date +%s`
    time_taken=`expr $end - $start`
    echo "End of stage 8, Execution time was $time_taken seconds."
fi

exit
