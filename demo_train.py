# -*- coding: utf-8 -*-
# @Time    : 2019/4/20 20:36
# @Author  : LegenDong
# @User    : legendong
# @File    : demo_train.py
# @Software: PyCharm
import argparse
import os
import random

import numpy as np
import torch
from torch import optim
from torch.utils.data import DataLoader

from datasets import IQiYiFaceDataset
from models import TestModel, FocalLoss
from utils import check_exists, save_model, weighted_average_pre_progress


def main(data_root, save_dir):
    if not check_exists(save_dir):
        os.makedirs(save_dir)

    dataset = IQiYiFaceDataset(data_root, 'train',
                               pre_progress=weighted_average_pre_progress)
    data_loader = DataLoader(dataset, batch_size=4096, shuffle=True, num_workers=4)
    log_step = len(data_loader) // 10 if len(data_loader) > 10 else 1

    model = TestModel()
    loss_func = FocalLoss()

    optimizer = optim.SGD(model.parameters(), lr=1e-1, momentum=0.9, weight_decay=1e-5)
    lr_scheduler = optim.lr_scheduler.StepLR(optimizer, 20)

    device = torch.device('cuda:0' if torch.cuda.is_available() else 'cpu')
    model = model.to(device)

    for epoch_idx in range(200):
        total_loss = .0
        for batch_idx, (feats, labels, _) in enumerate(data_loader):
            feats = feats.to(device)
            labels = labels.to(device)

            optimizer.zero_grad()

            output = model(feats, labels)
            loss = loss_func(output, labels)
            loss.backward()

            optimizer.step()
            total_loss += loss.item()

            if batch_idx % log_step == 0 and batch_idx != 0:
                print('Epoch: {} [{}/{} ({:.0f}%)] Loss: {:.6f}'
                      .format(epoch_idx, batch_idx * 4096, len(dataset),
                              100.0 * batch_idx / len(data_loader), loss.item()))
        log = {'epoch': epoch_idx,
               'lr': optimizer.param_groups[0]['lr'],
               'loss': total_loss / len(data_loader)}

        for key, value in sorted(log.items(), key=lambda item: item[0]):
            print('    {:20s}: {:6f}'.format(str(key), value))

        lr_scheduler.step()

        save_model(model, save_dir, 'test_model', epoch_idx)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='PyTorch Template')

    parser.add_argument('-r', '--root', default='/data/dcq/DataSets/iQIYI/', type=str,
                        help='path to load data (default: /data/dcq/DataSets/IQIYI/)')
    parser.add_argument('-s', '--save_dir', default='/data/dcq/Models/iQIYI/', type=str,
                        help='path to save model (default: /data/dcq/Models/IQIYI/)')
    parser.add_argument('-d', '--device', default=None, type=str,
                        help='indices of GPUs to enable (default: all)')

    args = parser.parse_args()

    if args.device:
        os.environ["CUDA_VISIBLE_DEVICES"] = args.device

    SEED = 0
    random.seed(SEED)
    np.random.seed(SEED)
    torch.manual_seed(SEED)
    torch.cuda.manual_seed(SEED)

    main(args.root, args.save_dir)