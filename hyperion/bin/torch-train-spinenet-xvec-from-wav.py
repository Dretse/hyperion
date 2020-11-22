#!/usr/bin/env python
"""
 Copyright 2020 Johns Hopkins University  (Author: Jesus Villalba)
 Apache 2.0  (http://www.apache.org/licenses/LICENSE-2.0)
"""
import sys
import os
import argparse
import time
import logging

import numpy as np

import torch
import torch.nn as nn

from hyperion.hyp_defs import config_logger, set_float_cpu
from hyperion.torch.utils import open_device
from hyperion.torch.helpers import OptimizerFactory as OF
from hyperion.torch.lr_schedulers import LRSchedulerFactory as LRSF
from hyperion.torch.seq_embed import SpineNetXVector as XVec
from hyperion.torch.trainers import XVectorTrainerFromWav as Trainer
from hyperion.torch.data import AudioDataset as AD
from hyperion.torch.data import ClassWeightedSeqSampler as Sampler
from hyperion.torch.metrics import CategoricalAccuracy

from hyperion.torch.layers import AudioFeatsFactory as AFF
from hyperion.torch.layers import MeanVarianceNorm as MVN

class FeatExtractor(nn.Module):

    def __init__(self, feat_extractor, mvn=None):
        super().__init__()

        self.feat_extractor = feat_extractor
        self.mvn = mvn

    def forward(self, x):
        f = self.feat_extractor(x)
        if self.mvn is not None:
            f = self.mvn(f)

        f = f.transpose(1,2).contiguous()
        return f


def train_xvec(audio_path, train_list, val_list, 
               train_aug_cfg, val_aug_cfg,
               num_gpus, resume, num_workers, **kwargs):

    set_float_cpu('float32')
    logging.info('initializing devices num_gpus={}'.format(num_gpus))
    device = open_device(num_gpus=num_gpus)

    ad_args = AD.filter_args(**kwargs)
    sampler_args = Sampler.filter_args(**kwargs)
    feat_args = AFF.filter_args(prefix='feats', **kwargs)
    mvn_args = MVN.filter_args(prefix='mvn', **kwargs)
    xvec_args = XVec.filter_args(**kwargs)
    opt_args = OF.filter_args(prefix='opt', **kwargs)
    lrsch_args = LRSF.filter_args(prefix='lrsch', **kwargs)
    trn_args = Trainer.filter_args(**kwargs)
    logging.info('audio dataset args={}'.format(ad_args))
    logging.info('sampler args={}'.format(sampler_args))
    logging.info('feat args={}'.format(feat_args))
    logging.info('mvn args={}'.format(mvn_args))
    logging.info('xvector network args={}'.format(xvec_args))
    logging.info('optimizer args={}'.format(opt_args))
    logging.info('lr scheduler args={}'.format(lrsch_args))
    logging.info('trainer args={}'.format(trn_args))

    logging.info('initializing feature extractor')
    feat_extractor = AFF.create(**feat_args)
    mvn = None
    if mvn_args['norm_mean'] or mvn_args['norm_var']:
        logging.info('initializing short-time mvn')
        mvn = MVN(**mvn_args)

    feat_extractor = FeatExtractor(feat_extractor, mvn)

    logging.info('init datasets')
    train_data = AD(audio_path, train_list, aug_cfg=train_aug_cfg, **ad_args)
    val_data = AD(audio_path, val_list, aug_cfg=val_aug_cfg, is_val=True, **ad_args)

    logging.info('init samplers')
    train_sampler = Sampler(train_data, **sampler_args)
    val_sampler = Sampler(val_data, **sampler_args)

    largs = {'num_workers': num_workers, 'pin_memory': True} if num_gpus>0 else {}

    train_loader = torch.utils.data.DataLoader(
        train_data, batch_sampler = train_sampler, **largs)

    test_loader = torch.utils.data.DataLoader(
        val_data, batch_sampler = val_sampler, **largs)

    xvec_args['num_classes'] = train_data.num_classes
    model = XVec(**xvec_args)

    logging.info('feat-extractor={}'.format(feat_extractor))
    logging.info('x-vector-model={}'.format(model))

    optimizer = OF.create(model.parameters(), **opt_args)
    lr_sch = LRSF.create(optimizer, **lrsch_args)
    metrics = { 'acc': CategoricalAccuracy() }
    
    trainer = Trainer(model, feat_extractor, optimizer, 
                      device=device, metrics=metrics, lr_scheduler=lr_sch,
                      data_parallel=(num_gpus>1), **trn_args)
    if resume:
        trainer.load_last_checkpoint()
    trainer.fit(train_loader, test_loader)



if __name__ == '__main__':

    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        fromfile_prefix_chars='@',
        description='Train XVector with SpineNet encoder from audio files')

    parser.add_argument('--audio-path', required=True)
    parser.add_argument('--train-list', required=True)
    parser.add_argument('--val-list', required=True)

    AD.add_argparse_args(parser)
    Sampler.add_argparse_args(parser)

    parser.add_argument('--train-aug-cfg', default=None)
    parser.add_argument('--val-aug-cfg', default=None)

    parser.add_argument('--num-workers', type=int, default=5, 
                        help='num_workers of data loader')

    AFF.add_argparse_args(parser, prefix='feats')
    MVN.add_argparse_args(parser, prefix='mvn')

    XVec.add_argparse_args(parser)
    OF.add_argparse_args(parser, prefix='opt')
    LRSF.add_argparse_args(parser, prefix='lrsch')
    Trainer.add_argparse_args(parser)

    parser.add_argument('--num-gpus', type=int, default=1,
                        help='number of gpus, if 0 it uses cpu')
    parser.add_argument('--seed', type=int, default=1123581321, 
                        help='random seed')
    parser.add_argument('--resume', action='store_true', default=False,
                        help='resume training from checkpoint')
    parser.add_argument('-v', '--verbose', dest='verbose', default=1, 
                        choices=[0, 1, 2, 3], type=int)

    args = parser.parse_args()
    config_logger(args.verbose)
    del args.verbose
    logging.debug(args)

    torch.manual_seed(args.seed)
    del args.seed

    train_xvec(**vars(args))


