# Copyright
#            2018   Johns Hopkins University (Author: Jesus Villalba)
#
# Paths to the databases used in the experiment

if [ "$(hostname --domain)" == "clsp.jhu.edu" ];then
  poison_full_root=$poison_path
  #/export/b17/xli257/poison
  musan_root=$musan_path
else
  poison_full_root=$poison_path
  #/export/b17/xli257/poison
  musan_root=$musan_path
fi


