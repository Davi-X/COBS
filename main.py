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
from cobs.predictive_model.pkl_importer import pklImporter
from tqdm import tqdm
from pprint import pprint

import torch
import torch.nn as nn
import torch.optim as optim
import torch.nn.functional as F

from config import state_names, disturbances_dict, eplus_naming_dict, eplus_var_types, SatAction
from agents.DQNAgent import *
from agents.Networks.DeepQ import *


def vectorise(curr_obs, dist_names, last_episode_obs_history, target_names=state_names):
    values = []
    VAV_1 = []
    VAV_2 = []
    VAV_3 = []
    VAV_5 = []
    disturbance = last_episode_obs_history[dist_names]
    all_exp_time = disturbance.index
    disturbance = (disturbance - disturbance.min()) / (disturbance.max() - disturbance.min())

    for name in target_names:
        if isinstance(name, str) and name in curr_obs:
            # For 'time' feature, to keep cyclical nature, convert to sin & cos for each time variable
            if name == 'time':
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
        # Currently, only for temp in each zone
        elif isinstance(name, dict):
            for feature, zones in name.items():
                if feature not in curr_obs:
                    continue

                history_in_dict = {zone: list() for zone in zones}
                col = last_episode_obs_history[feature]

                # List of dict to dict of list
                for i in range(len(last_episode_obs_history)):
                    for zone, value in col[i].items():
                        history_in_dict[zone].append(value)

                # For each zone, using history to min-max normalize and append to results
                for zone, value in curr_obs[feature].items():
                    if zone not in curr_obs[feature]:
                        continue
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

    # Add all environmental disturbances
    for i in range(len(disturbance)):
        if curr_obs['time'] == all_exp_time[i].to_pydatetime():
            values += list(disturbance.iloc[i].values)
    return values, [VAV_1, VAV_2, VAV_3]


def setup_env(idf_path, epw_path, season, forecast_path, planstep=12, num_days=14, timestep=4):
    #     reward = ViolationPActionReward(1)
    reward = Reward()

    ep_model = Model(
        idf_file_name=idf_path,
        weather_file=epw_path,
        eplus_naming_dict=eplus_naming_dict,
        eplus_var_types=eplus_var_types,
        reward=reward,
    )
    if season == 'summer':
        reheat = 0
        heat = 0
        cool = 1
        start_month = 7
    elif season == 'winter':
        reheat = 1
        heat = 1
        cool = 0
        start_month = 1
    else:
        raise ValueError(f"{season} is not a valid season. Only 'summer' or 'winter' are acceptable")

    ep_model.edit_configuration('SCHEDULE:COMPACT', {'Name': 'ReheatCoilAvailSched'}, {
        'Field 4': reheat
    })
    ep_model.edit_configuration('SCHEDULE:COMPACT', {'Name': 'HeatingCoilAvailSched'}, {
        'Field 4': heat
    })
    ep_model.edit_configuration('SCHEDULE:COMPACT', {'Name': 'CoolingCoilAvailSched'}, {
        'Field 4': cool
    })
    ep_model.set_runperiod(*(num_days, 1991, start_month, 1))
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

    # Add forecast data from given path
    # In simulation, set to None
    if forecast_path:
        external_data = pklImporter(forecast_path, planstep=planstep)
        ep_model.add_state_modifier(external_data)
    return ep_model


def run_dqn_episode(model, agent_list, dist_names, last_episode_obs_history):
    observations = []
    sat_actions_list = []
    forecast_state = model.state_modifier.models[0].get_output_states()

    curr_obs = model.reset()
    observations.append(curr_obs)
    state, AHUs = vectorise(curr_obs, dist_names, last_episode_obs_history, state_names + forecast_state)
    step_sat_actions = []
    for i in range(len(agent_list)):
        # As agent_start / step returns (sat_action, [sat + mix1, sat + mix2, sat + mix3])
        # We only want sat_action
        sat_action, _ = agent_list[i].agent_start((state + AHUs[i], curr_obs, 0))
        step_sat_actions.append(sat_action)
        sat_actions_list.append(sat_action)
    sat_actions_list.append('|*|')
    while not model.is_terminate():
        env_actions = []
        stpt_actions = SatAction([step_sat_actions[0] + curr_obs['AHU1 MA Temp.'],
                                  step_sat_actions[1] + curr_obs['AHU2 MA Temp.'],
                                  step_sat_actions[2] + curr_obs['AHU3 MA Temp.']], curr_obs)
        env_actions.extend(stpt_actions)
        curr_obs = model.step(env_actions)
        observations.append(curr_obs)

        forecast_state = model.state_modifier.models[0].get_output_states()
        state, AHUs = vectorise(curr_obs, dist_names, last_episode_obs_history, state_names + forecast_state)

        step_sat_actions = []
        for i in range(len(agent_list)):
            feeding_state = (state + AHUs[i], curr_obs, curr_obs["timestep"])
            sat_action, _ = (agent_list[i].agent_step(curr_obs["reward"], feeding_state))
            step_sat_actions.append(sat_action)
            sat_actions_list.append(sat_action)
        sat_actions_list.append('|*|')

    return observations, sat_actions_list, agent_list


def run_bdqn_episode(model, agent, dist_names, last_episode_obs_history):
    observations = []
    sat_actions_list = []
    forecast_state = model.state_modifier.models[0].get_output_states()

    curr_obs = model.reset()
    observations.append(curr_obs)
    state, AHUs = vectorise(curr_obs, dist_names, last_episode_obs_history, state_names + forecast_state)

    sat_action_tuples, _ = agent.agent_start((state + AHUs[0] + AHUs[1] + AHUs[2], curr_obs, 0))
    for AHU_sat in sat_action_tuples:
        sat_actions_list.append(AHU_sat[0])

    sat_actions_list.append('|*|')
    while not model.is_terminate():
        env_actions = []
        stpt_actions = SatAction([AHU_sat[1] for AHU_sat in sat_action_tuples], curr_obs)
        env_actions.extend(stpt_actions)

        curr_obs = model.step(env_actions)
        observations.append(curr_obs)

        forecast_state = model.state_modifier.models[0].get_output_states()
        state, AHUs = vectorise(curr_obs, dist_names, last_episode_obs_history, state_names + forecast_state)

        feeding_state = (state + AHUs[0] + AHUs[1] + AHUs[2], curr_obs, curr_obs["timestep"])
        sat_action_tuples, _ = agent.agent_step(curr_obs["reward"], feeding_state)
        for AHU_sat in sat_action_tuples:
            sat_actions_list.append(AHU_sat[0])
        sat_actions_list.append('|*|')

    return observations, sat_actions_list, agent
