# Copyright
#            2018   Johns Hopkins University (Author: Jesus Villalba)
#
# Paths to the databases used in the experiment

if [ "$(hostname --domain)" == "clsp.jhu.edu" ];then
  poison_full_root=$poison_path
  musan_root=$musan_path
else
  echo "Put your database paths here"
  exit 1
fi


