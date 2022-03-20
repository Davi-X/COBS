import os
import sys
import datetime

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

import os
# os.chdir("/mnt/c/Users/Dave/Project/COBS")
from cobs import Model, Reward
from cobs import OccupancyGenerator as OG
from tqdm import tqdm
from pprint import pprint

import torch
import torch.nn as nn
import torch.optim as optim
import torch.nn.functional as F

from config import state_names, eplus_naming_dict, eplus_var_types, SatAction
from agents.DQNAgent import *
from agents.Networks.DeepQ import *


def vectorise(curr_obs, agent_type, dist_names, last_episode_obs_history):
    values = []
    VAV_1 = []
    VAV_2 = []
    VAV_3 = []
    VAV_5 = []
    disturbance = last_episode_obs_history[dist_names]
    all_exp_time = disturbance.index
    disturbance = (disturbance - disturbance.min()) / (disturbance.max() - disturbance.min())

    for name in state_names:
        # Currently, only for temp in each zone
        if type(name) == dict:
            feature = list(name.keys())[0]
            zones = curr_obs[feature].keys()
            history_in_dict = {zone: list() for zone in zones}
            # List of dict to dict of list
            col = last_episode_obs_history[feature]
            for i in range(len(last_episode_obs_history)):
                for zone, value in col[i].items():
                    history_in_dict[zone].append(value)

            # For each zone, using history to min-max normalize and append to results
            for zone, value in curr_obs[feature].items():
                if agent_type == 'dqn':
                    zone_history = history_in_dict[zone]
                    normalised_zone_data = (value - min(zone_history)) / (max(zone_history) - min(zone_history))
                    values.append(normalised_zone_data)
                else:
                    if zone == 'Basement':
                        VAV_1.append(value)
                    elif 'bot' in zone or 'Ground' in zone:
                        VAV_2.append(value)
                    elif 'mid' in zone or 'Mid' in zone:
                        VAV_3.append(value)
                    elif 'top' in zone or 'Top' in zone:
                        VAV_5.append(value)
        # For time feature, to keep cyclical nature, convert to sin & cos for each time variable
        elif name == 'time':
            # curr_obs['time'] = curr_obs['time'].replace(year=1991)
            minutes_in_day = 24 * 60

            day_sin = np.sin(2 * np.pi * curr_obs['time'].day / 31)
            day_cos = np.cos(2 * np.pi * curr_obs['time'].day / 31)

            hour_sin = np.sin(2 * np.pi * curr_obs['time'].hour / 24)
            hour_cos = np.cos(2 * np.pi * curr_obs['time'].hour / 24)

            min_sin = np.sin(2 * np.pi * curr_obs['time'].minute / minutes_in_day)
            min_cos = np.cos(2 * np.pi * curr_obs['time'].minute / minutes_in_day)

            values += [day_sin, day_cos, hour_sin, hour_cos, min_sin, min_cos]
        else:
            values.append(curr_obs[name])

    if agent_type != 'dqn':
        VAV = [VAV_1, VAV_2, VAV_3, VAV_5]
        values.append(VAV)

    for i in range(len(disturbance)):
        if curr_obs['time'] == all_exp_time[i].to_pydatetime():
            values += list(disturbance.iloc[i].values)
    return values


def setup_env(idf_path, epw_path, num_days=14):
#     reward = ViolationPActionReward(1)
    reward = Reward()

    ep_model = Model(
        idf_file_name=idf_path,
        weather_file=epw_path,
        eplus_naming_dict=eplus_naming_dict,
        eplus_var_types=eplus_var_types,
        reward=reward,
    )
    ep_model.set_runperiod(*(num_days, 1991, 7, 1))

    return ep_model


def run_episode(model, agent, dist_names, last_episode_obs_history):
    observations = []
    sat_actions_list = []

    curr_obs = model.reset()
    observations.append(curr_obs)
    state = vectorise(curr_obs, 'dqn', dist_names, last_episode_obs_history)
    action = agent.agent_start((state, curr_obs, 0))

    while not model.is_terminate():
        env_actions = []
        stpt_actions = SatAction([action[0]], curr_obs)

        env_actions += stpt_actions

        curr_obs = model.step(env_actions)
        observations.append(curr_obs)
        state = vectorise(curr_obs, 'dqn', dist_names, last_episode_obs_history)

        feeding_state = (state, curr_obs, curr_obs["timestep"])
        action = agent.agent_step(curr_obs["reward"], feeding_state)
        sat_actions = action
        sat_actions_list.append(sat_actions[0])

    return observations, sat_actions_list, agent


def main():
    dist_names = ['Outdoor RH', 'Wind Speed', 'Wind Direction', 'Direct Solar Rad.', 'Diffuse Solar Rad.',
                  'Ambient Temp.']
    # Set Pre E+ simulation results
    dataset_name = "simulation_results/Sim-chicago.pkl"
    obs_history = pd.read_pickle(dataset_name)

    # Set E+ and IDF files paths
    Model.set_energyplus_folder("C:/Softwares/EnergyPlus/EnergyPlusV9-3-0/")
    idf_files_path = "C:/users/Dave/Downloads/idf-sample-files/"

    # Initialize the model with idf and weather files
    model = setup_env(idf_files_path + "2020/RefBldgLargeOfficeNew2004_Chicago.idf",
                      "cobs/data/weathers/USA_IL_Chicago-OHare.Intl.AP.725300_TMY3.epw")

    agent_params = {
        'gamma': 0.99,
        'epsilon': 0.1,
        'lr': 0.0001,
        'batch_size': 64,
        'eps_min': 0.1,
        'eps_dec': 0.001,
        'replace': 1000,
        'min_action': -20,
        # 'min_sat_action': -20,
        'max_action': 20,
        # 'max_sat_action': 20,
        'num_actions': 66,
        'mem_size': 200,
        'discrete_sat_actions': 66,
        'discrete_blind_actions': 33,
        'seed': 42
    }
    obs = model.reset()
    state = vectorise(obs, 'dqn', dist_names, obs_history)
    agent_params['input_dims'] = (len(state),)
    agent = DQNAgent(agent_params, DQN_Network)

    obs, actions, agent = run_episode(model, agent, dist_names, obs_history)


#     pprint(obs)
#     pprint(actions)
#     pprint(agent)


if __name__ == "__main__":

    main()

