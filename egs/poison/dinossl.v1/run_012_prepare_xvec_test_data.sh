#!/bin/bash
# Copyright
#                2020   Johns Hopkins University (Author: Jesus Villalba)
# Apache 2.0.
#
. ./cmd.sh
. ./path.sh
set -e

stage=2
config_file=default_config.sh

. parse_options.sh || exit 1;
. $config_file

#for validation
nnet_data=poison_test

if [ $stage -le 2 ]; then
    # This script preprocess audio for x-vector training
    steps_xvec/preprocess_audios_for_nnet_train.sh --nj 12 --cmd "$train_cmd" \
	--storage_name poison-dinossl.v1-$(date +'%m_%d_%H_%M') --use-bin-vad true \
	data/${nnet_data} data/${nnet_data}_proc_audio_no_sil exp/${nnet_data}_proc_audio_no_sil
    hyp_utils/kaldi/utils/fix_data_dir.sh data/${nnet_data}_proc_audio_no_sil
    hyp_utils/kaldi/utils/fix_data_dir.sh data/${nnet_data}

    

fi

if [ $stage -le 3 ]; then
    # Now, we remove files with less than 4s. This removes ~ 6.4% of the
    # number of the original samples for voxceleb2_train.
    echo "not removing the shorts files, because the dataset contains only 1sec segments."
    python copy_utt2dur.py data/${nnet_data} data/${nnet_data}_proc_audio_no_sil
    #hyp_utils/remove_short_audios.sh --min-len 4 data/${nnet_data}_proc_audio_no_sil
fi

if [ $stage -le 4 ]; then
    # Prepare train and validation lists for x-vectors. JJ: This might use
    # speaker labels but validation list won't be used in self-supervised
    # learning. (In the future, it may be used w/o labels for better validation)
    echo "not removing the silences, so the dataset contains same length segments."
    local/make_train_lists_sup_embed_with_augm.sh \
    data/${nnet_data} \
	data/${nnet_data}/lists_xvec
	#data/${nnet_data}_proc_audio_no_sil \
	#data/${nnet_data}_proc_audio_no_sil/lists_xvec
fi


exit
