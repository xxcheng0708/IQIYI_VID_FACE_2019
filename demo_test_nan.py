# -*- coding: utf-8 -*-
# @Time    : 2019-05-11 13:51
# @Author  : edward
# @File    : demo_test_nan.py
# @Software: PyCharm
import argparse
import logging
import os
import random

import numpy as np
import torch
from torch.utils.data import DataLoader

from datasets import IQiYiVidDataset
from models import ArcFaceNanModel
from utils import check_exists, default_get_result, init_logging, sep_cat_qds_vid_transforms

logger = logging.getLogger(__name__)


def main(data_root, num_frame, num_attn, moda, epoch):
    load_path = './checkpoints/demo_arcface_{}_nan_model_{:0>4d}.pth'.format(moda, epoch)
    assert check_exists(load_path)

    dataset = IQiYiVidDataset(data_root, 'test', moda, transform=sep_cat_qds_vid_transforms, num_frame=num_frame)
    data_loader = DataLoader(dataset, batch_size=2048, shuffle=False, num_workers=0)

    model = ArcFaceNanModel(512 + 2, 10034 + 1, num_attn=num_attn)
    metric_func = torch.nn.Softmax(-1)

    logger.info('load model from {}'.format(load_path))
    state_dict = torch.load(load_path, map_location='cpu')
    model.load_state_dict(state_dict)

    device = torch.device('cuda:0' if torch.cuda.is_available() else 'cpu')
    model = model.to(device)

    logger.info('test model on {}'.format(device))

    model.eval()
    all_results = []
    outputs = []

    with torch.no_grad():
        for batch_idx, (feats, _, video_names) in enumerate(data_loader):
            logger.info('Test Model: {}/{}'.format(batch_idx, len(data_loader)))

            feats = feats.to(device)
            output = model(feats)
            output = metric_func(output)

            results = default_get_result(output.cpu(), video_names)
            outputs.append(output.cpu())
            all_results += list(results)
    outputs = torch.cat(outputs, dim=0)
    return all_results, outputs


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='PyTorch Template')
    parser.add_argument('--data_root', default='/data/materials/', type=str,
                        help='path to load data (default: /data/materials/)')
    parser.add_argument('--device', default=None, type=str, help='indices of GPUs to enable (default: all)')
    parser.add_argument('--log_root', default='/data/logs/', type=str,
                        help='path to save log (default: /data/logs/)')
    parser.add_argument('--result_root', default='/data/result/', type=str,
                        help='path to save result (default: /data/result/)')
    parser.add_argument('--num_frame', default=40, type=int, help='size of video length (default: 40)')
    parser.add_argument('--num_attn', default=1, type=int, help='number of attention block in NAN')
    parser.add_argument('--moda', default='face', type=str, help='modal[face, head] of model train, (default: face)')
    parser.add_argument('--epoch', type=int, default=100, help="the epoch num for train (default: 100)")

    args = parser.parse_args()

    if args.device:
        os.environ["CUDA_VISIBLE_DEVICES"] = args.device

    SEED = 0
    random.seed(SEED)
    np.random.seed(SEED)
    torch.manual_seed(SEED)
    torch.cuda.manual_seed(SEED)

    log_root = args.log_root
    result_root = args.result_root

    result_log_path = os.path.join(log_root, 'result_log.txt')
    result_path = os.path.join(result_root, 'result.txt')
    log_path = os.path.join(log_root, 'log.txt')

    if check_exists(result_log_path):
        os.remove(result_log_path)
    if check_exists(result_path):
        os.remove(result_path)
    if check_exists(log_path):
        os.remove(log_path)

    init_logging(log_path)

    all_results, outputs = main(args.data_root, args.num_frame, args.num_attn, args.moda, args.epoch)
    max_value_video_idx = torch.argmax(outputs, dim=0)

    results_dict = {}
    for result in all_results:
        key = result[0].int().item()
        if key not in results_dict.keys():
            results_dict[key] = [(*result[1:],)]
        else:
            results_dict[key].append((*result[1:],))

    with open(result_path, 'w', encoding='utf-8') as f:
        for i in range(1, 10035):
            value = results_dict.get(i, None)
            if value is None:
                idx = max_value_video_idx[i]
                video_names_str = '{}.mp4'.format(all_results[idx][2])
                f.write('{} {}\n'.format(i, video_names_str))
            else:
                value.sort(key=lambda k: k[0], reverse=True)
                value = ['{}.mp4'.format(i[1]) for i in value[:100]]
                video_names_str = ' '.join(value)
                f.write('{} {}\n'.format(i, video_names_str))

    with open(result_log_path, 'w', encoding='utf-8') as f:
        for i in range(1, 10035):
            value = results_dict.get(i, None)
            if value is None:
                idx = max_value_video_idx[i]
                video_names_str = '{}.mp4'.format(all_results[idx][2])
                f.write('{} {}\n'.format(i, video_names_str))
            else:
                value.sort(key=lambda k: k[0], reverse=True)
                value = ['{}.mp4'.format(i[1]) for i in value[:100]]
                video_names_str = ' '.join(value)
                f.write('{} {}\n'.format(i, video_names_str))