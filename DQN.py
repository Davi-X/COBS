import random
import sys
import datetime

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

import os
from os.path import exists
from setting import eplus_naming_dict, eplus_var_types
from cobs import Model, Reward
from cobs import OccupancyGenerator as OG
from tqdm import tqdm
from pprint import pprint

import torch
import torch.nn as nn
import torch.optim as optim
import torch.nn.functional as F

# Set E+ and IDF files paths
Model.set_energyplus_folder("/Users/Dave/Project/EnergyPlus-9-3-0/")
idf_files_path = "/Users/Dave/Downloads/idf-sample-files/"

# Initialize the model with idf and weather files
reward = Reward()
model = Model(idf_file_name=idf_files_path+"2020/RefBldgLargeOfficeNew2004_Chicago.idf",
              weather_file="cobs/data/weathers/USA_IL_Chicago-OHare.Intl.AP.725300_TMY3.epw",
              eplus_naming_dict=eplus_naming_dict,
              eplus_var_types=eplus_var_types,
              reward=reward)

# class DQN(nn.Module):
#     def __init__(self, num_features, num_actions):
#         super().__init__()
#
#         self.fc1 = nn.Linear(num_features, 24)
#         self.fc2 = nn.Linear(24, 32)
#         self.fc3 = nn.Linear(32, 32)
#         self.out = nn.Linear(32, num_actions)
#
#     def forward(self, t):
#         t = t.Flatten(start_dim=1)
#         t = F.relu(self.fc1(t))
#         t = F.relu(self.fc2(t))
#         t = F.relu(self.fc3(t))
#         t = self.out(t)
#         return t
#
# class EplisonGreedyStrategy():
#     def __init__(self, start, end, decay):
#         self.start = start
#         self.end = end
#         self.decay = decay
#     def get_exploration_rate(self, current_step):
#         return self.end + (self.start - self.end) * math.exp(-1. * current_step * self.decay)
#
# class Agent():
#     def __init__(self, strategy):
#         self.strategy = strategy
#
#     def select_action(self, state, policy_net):
#         eplison = strategy.get_exploration_rate()
#         if eplison > random.random():
#             action = random.randrange(self.num_actions)
#
#
# batch_size = 256
# gamma = 0.999
# eps_start = 1
# eps_end = 0.01
# eps_decay = 0.001
# target_update = 10
# memory_size = 100000
# lr = 0.001
# num_episodes = 100
#
# state = model.reset()
# num_input = len(state['temperature']) + 4
# device = torch.device("cuda" if torch.cuda.is_available() elese "cpu")
# strategy = EplisonGreedyStrategy(eps_start, eps_end, eps_decay)
# agent = Agent(strategy, #actions, device)
#
# policy_net = DQN(num_input).to(device)
# target_net = DQN().to(device)
# target_net.load_state_dict(policy_net.stat_dict())
# target_net.eval()
# optimizer = optim.Adam(params=policy_net.parameters(), lr=lr)
#
# for episode in range(num_episodes):
#     state = model.reset()

def main():
    model.reset()
    # model.step()
    # state = model.step()
    # print(model.reward, model.prev_reward)
    # print(state)
    return
if __name__ == "__main__":
    main()
