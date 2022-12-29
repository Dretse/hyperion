import sys
from tqdm import tqdm
import os

# get args
dataset_path, fs, out_dir = sys.argv[1], sys.argv[2], sys.argv[3]
if not os.path.exists(out_dir): os.mkdir(out_dir)

spkr_file = out_dir+"/utt2spk"
other_spkr_file = out_dir+"/spk2utt"
wav_file = out_dir+"/wav.scp"

#clean files
if os.path.exists(spkr_file): open(spkr_file, 'w').close()
if os.path.exists(other_spkr_file): open(other_spkr_file, 'w').close()
if os.path.exists(wav_file):  open(wav_file,  'w').close()

#write files
for dir_n in tqdm(range(12)):
  dir=str(dir_n)
  files = os.listdir(os.path.join(dataset_path, dir))
  with open(spkr_file, "a") as new_file:
    new_file.writelines([f"{dir}-{file.split('.')[0]} {dir}\n" for file in files])
  with open(wav_file, "a") as new_file:
    new_file.writelines([f"{dir}-{file.split('.')[0]} {dataset_path}/{dir}/{file}\n" for file in files])

#check duplicates and sort
def duplicates_and_sort(filename):
  with open(filename, 'r') as file:
    lines = file.readlines()
  if (len(lines)!=len(set(lines))):
    print("Duplicates found")
    lines = list(set(lines))
  with open(filename, 'w') as file:
    file.writelines(sorted(lines))

duplicates_and_sort(spkr_file)
duplicates_and_sort(wav_file)

os.system(f"utils/utt2spk_to_spk2utt.pl {out_dir}/utt2spk >{out_dir}/spk2utt")
"""
foreach (@spkr_dirs) {
  my $spkr_id = $_;
  opendir my $dh, "$dataset_path/$spkr_id/" or die "Cannot open directory: $!";
  my @files = map{s/\.[^.]+$//;$_}grep {/\.wav$/} readdir($dh);
  closedir $dh;

  foreach (@files) {
    my $name = $_;
    my $wav = "ffmpeg -v 8 -i $dataset_path/$spkr_id/$name.wav -f wav -acodec pcm_s16le - |";
    if($fs == 8){
        $wav = $wav." sox -t wav - -t wav -r 8k - |"
    }
    my $utt_id = "$spkr_id-$name";
    print WAV "$utt_id", " $wav", "\n";
    print SPKR "$utt_id", " $spkr_id", "\n";
  }
}
close(SPKR) or die;
close(WAV) or die;

if (system(
  "utils/utt2spk_to_spk2utt.pl $out_dir/utt2spk >$out_dir/spk2utt") != 0) {
  die "Error creating spk2utt file in directory $out_dir";
}
system("env LC_COLLATE=C utils/fix_data_dir.sh $out_dir");
if (system("env LC_COLLATE=C utils/validate_data_dir.sh --no-text --no-feats $out_dir") != 0) {
  die "Error validating directory $out_dir";
}
"""