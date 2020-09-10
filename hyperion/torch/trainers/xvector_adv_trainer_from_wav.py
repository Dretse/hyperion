"""
 Copyright 2019 Johns Hopkins University  (Author: Jesus Villalba)
 Apache 2.0  (http://www.apache.org/licenses/LICENSE-2.0)
"""
import os
from collections import OrderedDict as ODict

import time
import logging

import torch
import torch.nn as nn

from ..utils import MetricAcc, TorchDataParallel
from .xvector_trainer_from_wav import XVectorTrainerFromWav


class XVectorAdvTrainerFromWav(XVectorTrainerFromWav):
    """Adversarial Training of x-vectors with attack in feature domain

       Attributes:
         model: x-Vector model object.
         feat_extractor: feature extractor nn.Module
         optimizer: pytorch optimizer object
         attack: adv. attack generator object
         epochs: max. number of epochs
         exp_path: experiment output path
         cur_epoch: current epoch
         grad_acc_steps: gradient accumulation steps to simulate larger batch size.
         p_attack: attack probability
         device: cpu/gpu device
         metrics: extra metrics to compute besides cxe.
         lr_scheduler: learning rate scheduler object
         loggers: LoggerList object, loggers write training progress to std. output and file.
                  If None, it uses default loggers.
         data_parallel: if True use nn.DataParallel
         loss: if None, it uses cross-entropy
         train_mode: training mode in ['train', 'ft-full', 'ft-last-layer']
         use_amp: uses mixed precision training.
         log_interval: number of optim. steps between log outputs
    """

    def __init__(self, model, feat_extractor, optimizer, attack, epochs, exp_path, cur_epoch=0, 
                 grad_acc_steps=1, p_attack=0.8,
                 device=None, metrics=None, lr_scheduler=None, loggers=None, 
                 data_parallel=False, loss=None, train_mode='train', use_amp=False,
                 log_interval=10):

        super().__init__(
            model, feat_extractor, optimizer, epochs, exp_path, cur_epoch=cur_epoch,
            grad_acc_steps=grad_acc_steps, device=device, metrics=metrics,
            lr_scheduler=lr_scheduler, loggers=loggers, data_parallel=data_parallel, 
            loss=loss, train_mode=train_mode, use_amp=use_amp,
            log_interval=log_interval)

        self.attack = attack
        self.p_attack = p_attack*self.grad_acc_steps
        if self.p_attack > 1:
            logging.warning((
                'p-attack(%f) cannot be larger than 1./grad-acc-steps (%f)'
                'because we can only create adv. signals in the '
                'first step of the gradient acc. loop given that'
                'adv optimization over-writes the gradients '
                'stored in the model') % (p_attack, 1./self.grad_acc_steps))

        if data_parallel:
            # change model in attack by the data parallel version
            self.attack.model = TorchDataParallel(self.attack.model)
            # make loss function in attack data parallel
            self.attack.make_data_parallel()

        
    def train_epoch(self, data_loader):
        
        self.model.update_loss_margin(self.cur_epoch)

        metric_acc = MetricAcc()
        batch_metrics = ODict()
        if self.train_mode == 'train':
            self.model.train()
        else:
            self.model.train_mode(self.train_mode)

        for batch, (data, target) in enumerate(data_loader):
            self.loggers.on_batch_begin(batch)
            
            data, target = data.to(self.device), target.to(self.device)
            batch_size = data.shape[0]

            if batch % self.grad_acc_steps == 0:
                if torch.rand(1) < self.p_attack:
                    # generate adversarial attacks
                    logging.info('generating adv attack for batch=%d' % (batch))
                    self.model.eval()
                    data1 = self.attack.generate(data, target)
                    max_delta = torch.max(torch.abs(data1-data)).item()
                    logging.info('adv attack max perturbation=%f' % (max_delta))
                    data = data1
                    if self.train_mode == 'train':
                        self.model.train()
                    else:
                        self.model.train_mode(self.train_mode)

                self.optimizer.zero_grad()

            with torch.no_grad():
                feats = self.feat_extractor(data)

            output = self.model(feats, target)
            loss = self.loss(output, target).mean()/self.grad_acc_steps
            loss.backward()

            if (batch+1) % self.grad_acc_steps == 0:
                if self.lr_scheduler is not None:
                    self.lr_scheduler.on_opt_step()
                self.optimizer.step()

            batch_metrics['loss'] = loss.item() * self.grad_acc_steps
            for k, metric in self.metrics.items():
                batch_metrics[k] = metric(output, target)
            
                
            metric_acc.update(batch_metrics, batch_size)
            logs = metric_acc.metrics
            logs['lr'] = self._get_lr()
            self.loggers.on_batch_end(logs=logs, batch_size=batch_size)


        logs = metric_acc.metrics
        logs['lr'] = self._get_lr()
        return logs

                                             

    def validation_epoch(self, data_loader):

        metric_acc = MetricAcc()
        batch_metrics = ODict()

        self.model.eval()
        for batch, (data, target) in enumerate(data_loader):
            data, target = data.to(self.device), target.to(self.device)
            batch_size = data.shape[0]

            if torch.rand(1) < self.p_attack:
                # generate adversarial attacks
                data = self.attack.generate(data, target)

            with torch.no_grad():
                feats = self.feat_extractor(data)
                output = self.model(feats)
                loss = self.loss(output, target)

            batch_metrics['loss'] = loss.mean().item()
            for k, metric in self.metrics.items():
                batch_metrics[k] = metric(output, target)
            
            metric_acc.update(batch_metrics, batch_size)

        logs = metric_acc.metrics
        logs = ODict(('val_' + k, v) for k,v in logs.items())
        return logs

