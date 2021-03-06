'''
Author: Marianne Linhares, mariannelinharesm@gmail.com
Last Change: 08/2018

Based on the script from BGodefroyFR
at: https://github.com/BGodefroyFR/Deep-Audio-Visualization/blob/master/learning/scripts/downloadTrainingSamples.py
'''

from preprocessors.audio_preprocessor import AudioPreprocessor
from preprocessors.partition_preprocessor import PartitionPreprocessor

from collections import OrderedDict

import os
import glob
import argparse
import numpy as np
import pickle


parser = argparse.ArgumentParser('Preprocess waf files and partition dataset if needed.')

# Paths
parser.add_argument('--train-path', type=str, required=True)
parser.add_argument('--eval-path', type=str, default=None)
parser.add_argument('--test-path', type=str, default=None)
parser.add_argument('--output-path', type=str, default='audio_files/transfer/')
# Audio parameters
parser.add_argument('--format', type=str, default='melspectrogram',
                    choices=['spectrogram', 'melspectrogram'])
parser.add_argument('--n_fft', type=int, default=2048)
parser.add_argument('--sample-size', type=int, default=0.8)
parser.add_argument('--sample-type', type=str, default='all', choices=['all', 'random'])
# Others
parser.add_argument('--seed', type=int, default=7)
parser.add_argument('--test-size', type=int, default=0.25)


def build_data_partition(path, dp, classes, curr_index, n_fft, format, sample_size, sample_type):
    glob_path = os.path.join(path, '**', '*.wav')
    
    spectrograms = []
    labels = []
    
    glob_files = glob.glob(glob_path)
    for i, f in enumerate(glob_files):
        class_name = f.split('/')[-2]
        
        if class_name not in classes:
            classes[class_name] = curr_index
            curr_index += 1
        
        if i % 100 == 0:
            print('Preprocessing %d/%d, %.2f%% ...' % (i, len(glob_files), i/len(glob_files) * 100))
        
        f_splitted = AudioPreprocessor.split_wav_file(f, seconds=sample_size, sample_type=sample_type)
        for new_file in f_splitted:
            spectrogram = AudioPreprocessor.wav_file_to(new_file, n_fft, to=format)
            spectrograms.append(spectrogram)
            labels.append(classes[class_name])

    return spectrograms, labels, classes, curr_index


def build_wav_dataset(data_partitions_path, output_path, n_fft, format, test_size, sample_size, sample_type):
    classes = {}
    curr_index = 0

    data_partitions = {}    
    for dp in data_partitions_path:
        if data_partitions_path[dp] is None:
            train_data, test_data, train_labels, test_labels = PartitionPreprocessor.dataset_partition(data_partitions['train'][0],
                                                                                         data_partitions['train'][1],
                                                                                         test_size=test_size)
            data_partitions['train'] = (train_data, train_labels)
            data_partitions[dp] = (test_data, test_labels)
        else:
            spectrograms, labels, classes, curr_index = build_data_partition(data_partitions_path[dp], dp,
                                                                             classes, curr_index, n_fft, format,
                                                                             sample_size, sample_type)
            data_partitions[dp] = (np.array(spectrograms), np.array(labels))
    
    for dp in data_partitions:
        np.save(os.path.join(output_path, dp + '_data'), data_partitions[dp][0])
        np.save(os.path.join(output_path, dp + '_labels'), data_partitions[dp][1])
    
    
    with open(os.path.join(output_path, 'classes'), 'wb') as fp:
        pickle.dump(classes, fp, protocol=pickle.HIGHEST_PROTOCOL)


if __name__ == "__main__":
    args = parser.parse_args()
    np.random.seed(args.seed)
    data_partitions_path = OrderedDict({
        'train': args.train_path,
        'test': args.eval_path, 
        'eval': args.test_path
    })
    build_wav_dataset(data_partitions_path, args.output_path,
                      args.n_fft, args.format, args.test_size, args.sample_size,
                      args.sample_type)