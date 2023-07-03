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

if [ -z ${2+x} ]; then stage=1; else stage=$2; fi

export poison_path="/export/b17/xli257/poison_data_dumps/${1}" #replace this by the path to the poisoned dataset extracted

export poison_name=$1

export musan_path=/export/corpora5/JHU/musan

export new_poison_path=/export/b17/tthebau1/temp/${1}_test
if [ ! -d $new_poison_path ]; then mkdir $new_poison_path; fi

 
if [ $stage -le 1 ];then 
    echo "Starting stage 1"
    start=`date +%s`
    python from_pickledata_to_wavdata.py $poison_path 16000 $new_poison_path "test" || exit 1;
    end=`date +%s`
    time_taken=`expr $end - $start`
    echo "End of stage 1, Execution time was $time_taken seconds." #time measured: 3:31
fi

export dino_other=$1
export poison_name=${1}_test
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

if [ $stage -le 5 ];then 
    echo "### Preparing the training data, stage 5 ###"
    start=`date +%s`
    bash run_010_prepare_xvec_train_data.sh || exit 1;
    end=`date +%s`
    time_taken=`expr $end - $start`
    echo "End of stage 5, Execution time was $time_taken seconds." #time measured 44:42

fi

if [ $stage -le 7 ];then
    echo "### Extracting xvectors ### stage 7"
    start=`date +%s`
    bash run_030_extract_xvectors_test.sh || exit 1;
    end=`date +%s`
    time_taken=`expr $end - $start`
    echo "End of stage 7, Execution time was $time_taken seconds."
fi
