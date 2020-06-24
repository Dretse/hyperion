"""
 Copyright 2019 Johns Hopkins University  (Author: Jesus Villalba)
 Apache 2.0  (http://www.apache.org/licenses/LICENSE-2.0)
"""
import os
from collections import OrderedDict as ODict

import logging
#import numpy as np

import torch
import torch.nn as nn
from apex import amp

from ..utils import MetricAcc
from .torch_trainer import TorchTrainer, TorchDataParallel


class XVectorTrainerDeepFeatReg(TorchTrainer):

    def __init__(self, model, prior_model, optimizer, epochs, exp_path, cur_epoch=0, 
                 grad_acc_steps=1, reg_layers_enc=None, reg_layers_classif=None,
                 reg_weight_enc=0.1, reg_weight_classif=0.1,
                 device=None, metrics=None, lr_scheduler=None, loggers=None, 
                 data_parallel=False, loss=None, reg_loss=None, train_mode='train', use_amp=False):

        if loss is None:
            loss = nn.CrossEntropyLoss()

        super(XVectorTrainerDeepFeatReg, self).__init__(
            model, optimizer, loss, epochs, exp_path, cur_epoch=cur_epoch,
            grad_acc_steps=grad_acc_steps, device=device, metrics=metrics,
            lr_scheduler=lr_scheduler, loggers=loggers, data_parallel=data_parallel, 
            train_mode=train_mode, use_amp=use_amp)

        self.prior_model = prior_model
        if reg_loss is None:
            reg_loss = nn.L1Loss()
        self.reg_loss = reg_loss
        self.reg_layers_enc = reg_layers_enc
        self.reg_layers_classif = reg_layers_classif
        self.reg_weight_enc = reg_weight_enc
        self.reg_weight_classif = reg_weight_classif
        
        if device is not None:
            self.prior_model.to(device)
            self.reg_loss.to(device)
        
        if data_parallel:
            self.prior_model = TorchDataParallel(self.prior_model)
            self.reg_loss = TorchDataParallel(self.reg_loss)


        
    def train_epoch(self, data_loader):
        #epoch_batches = len(data_loader.dataset)
        #total_batches = self.cur_epoch * epoch_batches
        
        self.model.update_loss_margin(self.cur_epoch)

        metric_acc = MetricAcc()
        batch_metrics = ODict()
        if self.train_mode == 'train':
            self.model.train()
        else:
            self.model.train_mode(self.train_mode)

        for batch, (data, target) in enumerate(data_loader):
            self.loggers.on_batch_begin(batch)

            if batch % self.grad_acc_steps == 0:
                self.optimizer.zero_grad()
                
            data, target = data.to(self.device), target.to(self.device)
            batch_size = data.shape[0]

            h_enc, h_classif, output = self.model.forward_hid_feats(
                data, target, self.reg_layers_enc, self.reg_layers_classif, return_output=True)
            loss = self.loss(output, target).mean() # you need to take the mean here because of the multi-gpu training
            batch_metrics['loss-classif'] = loss.item()
            
            prior_h_enc, prior_h_classif = self.prior_model.forward_hid_feats(
                data, target, self.reg_layers_enc, self.reg_layers_classif, return_output=False)

            n_enc = len(h_enc)
            if n_enc > 0:
                loss_scale = self.reg_weight_enc/n_enc
            for i in range(n_enc):
                l = self.reg_layers_enc[i]
                loss_i = self.reg_loss(h_enc[i], prior_h_enc[i]).mean()
                loss_name = 'reg-h-enc-%d' % l
                batch_metrics[loss_name] = loss_i.item()
                loss += loss_scale * loss_i

            n_classif = len(h_classif)
            if n_classif > 0:
                loss_scale = self.reg_weight_classif/n_classif
            for i in range(n_classif):
                l = self.reg_layers_classif[i]
                loss_i = self.reg_loss(h_classif[i], prior_h_classif[i]).mean()
                loss_name = 'reg-h-classif-%d' % l
                batch_metrics[loss_name] = loss_i.item()
                loss += loss_scale * loss_i

            batch_metrics['loss'] = loss.item()  
            loss = loss/self.grad_acc_steps
            if self.use_amp:
                with amp.scale_loss(loss, self.optimizer) as scaled_loss:
                    scaled_loss.backward()
            else:
                loss.backward()

            if (batch+1) % self.grad_acc_steps == 0:
                if self.lr_scheduler is not None:
                    self.lr_scheduler.on_opt_step()
                self.optimizer.step()

            for k, metric in self.metrics.items():
                batch_metrics[k] = metric(output, target)
            
            metric_acc.update(batch_metrics, batch_size)
            logs = metric_acc.metrics
            logs['lr'] = self._get_lr()
            self.loggers.on_batch_end(logs=logs, batch_size=batch_size)
            #total_batches +=1

        logs = metric_acc.metrics
        logs['lr'] = self._get_lr()
        return logs

                                             

