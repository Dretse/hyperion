#!/bin/bash
# Copyright
#                2018   Johns Hopkins University (Author: Jesus Villalba)
# Apache 2.0.
#
. ./cmd.sh
. ./path.sh
set -e

stage=1
config_file=default_config.sh

. parse_options.sh || exit 1;
. datapath.sh 

if [ $stage -le 1 ];then
  # Prepare the poisoned dataset for training.
  #python local/make_poison.py $poison_train_root 16 data/poison_train
  #python local/make_poison.py $poison_test_root 16 data/poison_test
  python local/make_poison.py $poison_full_root 16 "data/${poison_name}"
fi


