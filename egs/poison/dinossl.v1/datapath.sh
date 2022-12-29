# Copyright
#            2018   Johns Hopkins University (Author: Jesus Villalba)
#
# Paths to the databases used in the experiment

if [ "$(hostname --domain)" == "clsp.jhu.edu" ];then
  poison_full_root=/export/b17/xli257/poison
  musan_root=/export/corpora5/JHU/musan
else
  echo "Put your database paths here"
  exit 1
fi


