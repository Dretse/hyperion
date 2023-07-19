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

exps=( source11_target2_5_p10_und \
        source11_target2_p10_triggerMUSANmusic_full \
        source11_target2_p10_triggerMUSANmusic \
        source11_target2_p10_triggerNonMUSANmusic \
        source11_target2_p10_und \
        source11_target5_p10_und \
        source3_target2_p10_und \
        source3_target5_p10_und \
        trigger2_und \
        source11_target2_p10_scale0.02 \
        source11_target2_p10_scale0.5 \
        random_und )

for name in "${exps[@]}"; do
    class_attacked=1
    if [[ $name == 'source11_target2_5_p10_und' ]]; then class_attacked=2; fi
    echo $name
    echo $class_attacked
done

for name in "${exps[@]}"; do
    
    class_attacked=1
    if [[ $name == 'source11_target2_5_p10_und' ]]; then class_attacked=2; fi

    echo "Doing clustering for exp ${name} Hypothesis: $class_attacked classes attacked"

    export poison_path="/export/b17/xli257/poison_data_dumps/${name}" #replace this by the path to the poisoned dataset extracted
    export poison_name=$name
    export musan_path=/export/corpora5/JHU/musan
    export new_poison_path=/export/b17/tthebau1/temp/$name
    export poison_path=$new_poison_path
    
    start=`date +%s`
    python clustering.py 1000 $class_attacked "exp/xvectors/fbank80_stmn_lresnet34_e256_do0_b48_amp.dinossl.v1/${poison_name}" ${poison_name} || exit 1;
    end=`date +%s`
    time_taken=`expr $end - $start`
    echo "End of stage 8, Execution time was $time_taken seconds."

done