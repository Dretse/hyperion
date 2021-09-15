#!/usr/bin/env python
"""
  Copyright 2019 Johns Hopkins University  (Author: Jesus Villalba)
  Apache 2.0  (http://www.apache.org/licenses/LICENSE-2.0)  

  Trains Backend for SRE18 video condition
"""

import sys
import os
import argparse
import time
import logging
from jsonargparse import ArgumentParser, namespace_to_dict

import numpy as np
import pandas as pd

from hyperion.hyp_defs import float_cpu, config_logger
from hyperion.helpers import VectorClassReader as VCR
from hyperion.transforms import TransformList, LDA, LNorm
from hyperion.helpers import PLDAFactory as F
from hyperion.utils.scp_list import SCPList


def train_be(
    v_file,
    train_list,
    lda_dim,
    plda_type,
    y_dim,
    z_dim,
    epochs,
    ml_md,
    md_epochs,
    output_path,
    **kwargs
):

    # Read data
    vcr_args = VCR.filter_args(**kwargs)
    vcr_train = VCR(v_file, train_list, None, **vcr_args)
    x, class_ids = vcr_train.read()

    # Train LDA
    t1 = time.time()

    lda = LDA(lda_dim=lda_dim, name="lda")
    lda.fit(x, class_ids)

    x_lda = lda.predict(x)
    logging.info("LDA Elapsed time: %.2f s." % (time.time() - t1))

    # Train centering and whitening
    t1 = time.time()
    lnorm = LNorm(name="lnorm")
    lnorm.fit(x_lda)

    x_ln = lnorm.predict(x_lda)
    logging.info("LNorm Elapsed time: %.2f s." % (time.time() - t1))

    # Train PLDA
    t1 = time.time()

    plda = F.create_plda(plda_type, y_dim=y_dim, z_dim=z_dim, name="plda")
    elbo = plda.fit(x_ln, class_ids, epochs=epochs, ml_md=ml_md, md_epochs=md_epochs)

    logging.info("PLDA Elapsed time: %.2f s." % (time.time() - t1))

    # Save models
    preproc = TransformList(lda)
    preproc.append(lnorm)

    if not os.path.exists(output_path):
        os.makedirs(ouput_path)

    preproc.save(output_path + "/lda_lnorm.h5")
    plda.save(output_path + "/plda.h5")

    elbo = pd.DataFrame(
        {"epoch": np.arange(epochs), "elbo": elbo[0], "elbo_per_sample": elbo[1]}
    )
    elbo.to_csv(output_path + "/elbo.csv", sep=",", index=False)


if __name__ == "__main__":

    parser = ArgumentParser(
        description="Train LDA+LNorm+PLDA Back-end in single dataset"
    )

    parser.add_argument("--v-file", required=True)
    parser.add_argument("--train-list", required=True)

    VCR.add_class_args(parser)
    F.add_class_args(parser)

    parser.add_argument("--output-path", required=True)
    parser.add_argument("--lda-dim", type=int, default=None)
    parser.add_argument(
        "-v", "--verbose", dest="verbose", default=1, choices=[0, 1, 2, 3], type=int
    )

    args = parser.parse_args()
    config_logger(args.verbose)
    del args.verbose
    logging.debug(args)

    train_be(**namespace_to_dict(args))
