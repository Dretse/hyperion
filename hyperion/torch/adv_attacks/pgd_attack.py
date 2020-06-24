"""
 Copyright 2020 Johns Hopkins University  (Author: Jesus Villalba)
 Apache 2.0  (http://www.apache.org/licenses/LICENSE-2.0)
"""
from __future__ import absolute_import

#import logging

import torch

from .adv_attack import AdvAttack

class PGDAttack(AdvAttack):

    def __init__(self, model, eps, alpha, norm, max_iter=10, 
                 random_eps=False, num_random_init=0, loss=None, 
                 targeted=False, range_min=None, range_max=None):
        super(PGDAttack, self).__init__(
            model, loss, targeted, range_min, range_max)
        self.eps = eps
        self.alpha = alpha
        self.max_iter = max_iter
        self.norm = norm
        self.random_eps = random_eps
        self.num_random_init = num_random_init


    @staticmethod
    def _project(delta, eps, norm):

        if norm == 'inf' or norm == float('inf'):
            return torch.clamp(delta, -eps, eps)

        delta_tmp = torch.reshape(delta, (delta.shape[0], -1))
        one = torch.ones((1,), dtype=delta.dtype)
        if norm == 2:
            delta_tmp = delta_tmp*torch.min(
                one, eps/torch.norm(delta_tmp, dim=1, keepdim=True))
        elif norm == 1:
            delta_tmp = delta_tmp*torch.min(
                one, eps/torch.norm(delta_tmp, dim=1, keepdim=True, p=1))
        else:
            raise Exception('norm={} not supported'.format(norm))
        
        return torch.reshape(delta_tmp, delta.shape)


    @staticmethod
    def _random_sphere(shape, eps, norm, dtype, device):
        """We use Theorem 1 in https://arxiv.org/pdf/math/0503650.pdf
           to sample uniformly from l_p balls in R^n
        """

        if norm == 'inf' or norm == float('inf'):
            return 2*eps*(torch.rand(shape, dtype=dtype, device=device)-0.5)

        # Sample from exponential e^(-t) distribution
        u = torch.rand((shape[0],1), dtype=dtype, device=device)
        z = - (-u).log1p()

        if norm == 2:
            # sample from \propto exp(-|t|^p)
            u = torch.randn(shape, dtype=dtype, device=device).reshape(shape[0],-1)
            # compute norm
            l2 = torch.norm(u, dim=1, keepdim=True)
            # apply theorem and rescale norm
            x = eps * u / (l2**2 + z).sqrt()
        elif norm == 1:
            # sample from \propto exp(-|t|^p)
            u = torch.rand(shape, dtype=dtype, device=device).reshape(shape[0],-1)
            u = - (-u).log1p()
            # compute norm
            l1 = torch.norm(u, dim=1, keepdim=True, p=1)
            # apply theorem and rescale norm
            x = eps * u / (l1 + z)
        else:
            raise Exception('norm={} not supported'.format(norm))

        return x.reshape(shape)



    def generate(self, input, target):

        f = 1
        if self.targeted:
            f = -1
        
        if self.random_eps:
            eps = self.eps/2*torch.randn(1).item()
            alpha = eps*self.alpha/self.eps
        else:
            eps = self.eps
            alpha = self.alpha

        best_loss = None
        best_x = None

        for k in range(max(1, self.num_random_init)):
            x = input
            if self.num_random_init > 0:
                x = x + self._random_sphere(
                    x.shape, eps, self.norm , x.dtype, x.device) 
                x = self._clamp(x)

            for it in range(self.max_iter):
                x.detach_()
                x.requires_grad = True
                output = self.model(x)
                loss = self.loss(output, target).mean()
                self.model.zero_grad()
                loss.backward()
                dL_x = x.grad.data
                x = x + f * alpha * dL_x.sign()
                delta = self._project(x-input, eps, self.norm)
                x = input + delta

            x = self._clamp(x)
            if self.num_random_init < 2:
                best_x = x
            else:
                with torch.no_grad():
                    output = self.model(x)
                    loss = self.loss(output, target).mean().item()

                #if nontargeted we want higher loss, if targeted we want lower loss
                if best_loss is None or best_loss < f * loss:
                    best_x = x
                    best_loss = f * loss
            
        return best_x

        