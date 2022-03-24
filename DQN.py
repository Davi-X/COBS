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

from config import state_names, disturbances_dict, eplus_naming_dict, eplus_var_types, SatAction
from agents.DQNAgent import *
from agents.Networks.DeepQ import *


def vectorise(curr_obs, dist_names, last_episode_obs_history):
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
                zone_history = history_in_dict[zone]
                normalised_zone_data = (value - min(zone_history)) / (max(zone_history) - min(zone_history))
                # values.append(normalised_zone_data)

                # This is for DOE reference building Large Office Chicago
                # if zone == 'Basement':
                #     VAV_1.append(value)
                # elif 'bot' in zone or 'Ground' in zone:
                #     VAV_2.append(value)
                # elif 'mid' in zone or 'Mid' in zone:
                #     VAV_3.append(value)
                # elif 'top' in zone or 'Top' in zone:
                #     VAV_5.append(value)
                if 'bot' in zone or 'Ground' in zone or 'First' in zone:
                    VAV_1.append(normalised_zone_data)
                elif 'mid' in zone or 'Mid' in zone:
                    VAV_2.append(normalised_zone_data)
                elif 'top' in zone or 'Top' in zone:
                    VAV_3.append(normalised_zone_data)
        # For 'time' feature, to keep cyclical nature, convert to sin & cos for each time variable
        elif name == 'time':
            # curr_obs['time'] = curr_obs['time'].replace(year=1991)
            minutes_in_day = 24 * 60
            seconds_in_day = minutes_in_day * 60

            day_sin = np.sin(2 * np.pi * curr_obs['time'].day / 31)
            day_cos = np.cos(2 * np.pi * curr_obs['time'].day / 31)

            hour_sin = np.sin(2 * np.pi * curr_obs['time'].hour / 24)
            hour_cos = np.cos(2 * np.pi * curr_obs['time'].hour / 24)

            min_sin = np.sin(2 * np.pi * curr_obs['time'].minute / minutes_in_day)
            min_cos = np.cos(2 * np.pi * curr_obs['time'].minute / minutes_in_day)

            sec_sin = np.sin(2 * np.pi * curr_obs['time'].minute / seconds_in_day)
            sec_cos = np.cos(2 * np.pi * curr_obs['time'].minute / seconds_in_day)

            values += [day_sin, day_cos, hour_sin, hour_cos, min_sin, min_cos, sec_sin, sec_cos]
        else:
            values.append(curr_obs[name])

    # Add all environmental disturbances
    for i in range(len(disturbance)):
        if curr_obs['time'] == all_exp_time[i].to_pydatetime():
            values += list(disturbance.iloc[i].values)
    return values, [VAV_1, VAV_2, VAV_3]


def setup_env(idf_path, epw_path, num_days=14, timestep=4):
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
    ep_model.set_timestep(timestep)

    # Run Runperiod Time not the sizing periods
    original_run_period = {'Run_Simulation_for_Sizing_Periods': "YES",
                           'Run_Simulation_for_Weather_File_Run_Periods': "NO"}
    changed_run_period = {'Run_Simulation_for_Sizing_Periods': "NO",
                          'Run_Simulation_for_Weather_File_Run_Periods': "YES"}
    ep_model.edit_configuration("SimulationControl", original_run_period, changed_run_period)

    # Add Mixed Air Temp for each AHU to Output Variables
    ep_model.add_configuration("Output:Variable", {"Key Value": 'VAV_1_OA-VAV_1_CoolCNode',
                                                   "Variable Name": "System Node Temperature",
                                                   "Reporting Frequency": "Timestep"})

    ep_model.add_configuration("Output:Variable", {"Key Value": 'VAV_2_OA-VAV_2_CoolCNode',
                                                   "Variable Name": "System Node Temperature",
                                                   "Reporting Frequency": "Timestep"})

    ep_model.add_configuration("Output:Variable", {"Key Value": 'VAV_3_OA-VAV_3_CoolCNode',
                                                   "Variable Name": "System Node Temperature",
                                                   "Reporting Frequency": "Timestep"})
    # Add environmental disturbances variables
    existed_vars = [ep_model.idf.idfobjects["Output:Variable"][i].Variable_Name
                    for i in range(len(ep_model.idf.idfobjects["Output:Variable"]))]

    for dist_var in disturbances_dict.keys():
        if dist_var not in existed_vars:
            ep_model.add_configuration("Output:Variable", {"Variable Name": dist_var,
                                                           "Reporting Frequency": "Timestep"})
    return ep_model


def run_episode(model, agent_list, dist_names, last_episode_obs_history):
    observations = []
    sat_actions_list = []

    curr_obs = model.reset()
    observations.append(curr_obs)
    state, AHUs = vectorise(curr_obs, dist_names, last_episode_obs_history)
    actions = []
    for i in range(len(agent_list)):
        actions.append(agent_list[i].agent_start((state + AHUs[i], curr_obs, 0)))
        sat_actions_list.append(actions[i][0])
    sat_actions_list.append('|*|')
    while not model.is_terminate():
        env_actions = []
        stpt_actions = SatAction([actions[0][0] + curr_obs['AHU1 MA Temp.'],
                                  actions[1][0] + curr_obs['AHU2 MA Temp.'],
                                  actions[2][0] + curr_obs['AHU3 MA Temp.']], curr_obs)
        env_actions.extend(stpt_actions)
        curr_obs = model.step(env_actions)
        observations.append(curr_obs)
        state, AHUs = vectorise(curr_obs, dist_names, last_episode_obs_history)

        actions = []
        for i in range(len(agent_list)):
            feeding_state = (state + AHUs[i], curr_obs, curr_obs["timestep"])
            # print(curr_obs['timestep'])
            # print('--------------------------------------------------------------------------------------')
            # print(i, feeding_state)
            # print('--------------------------------------------------------------------------------------')
            actions.append(agent_list[i].agent_step(curr_obs["reward"], feeding_state))
            sat_actions_list.append(actions[i][0])
        sat_actions_list.append('|*|')
        # sat_actions = actions
        # sat_actions_list.append(sat_actions[0])

    return observations, sat_actions_list, agent_list


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

