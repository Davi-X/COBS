import numpy as np


def augment_ma(observation, action):
    """
    # The RL agent controls the difference between Supply Air Temp.
    and Mixed Air Temp., i.e. the amount of heating from the heating coil.
    But, the E+ expects Supply Air Temp. Setpoint... augment action to account for this
    """
    (last_state, obs_dict, cur_time) = observation
    # if action < 0:
    #     action = torch.zeros_like(action)
    SAT_zones = ["VAV1 MA Temp.", "VAV2 MA Temp.", "VAV3 MA Temp.", "VAV5 MA Temp."]
    SAT_stpt = [obs_dict[SAT_zone] + action for SAT_zone in SAT_zones]  # max(0, action)

    # If the room gets too warm during occupied period, uses outdoor air for free cooling.
    # if (obs_dict["Indoor Temp."] > obs_dict["Indoor Temp. Setpoint"]) & (obs_dict["Occupancy Flag"] == 1):
    #     SAT_stpt = obs_dict["Outdoor Temp."]

    return action, np.array(SAT_stpt)


def get_data_from_history(observations_history, key):
    data = []
    for i in range(len(observations_history)):
        data.append(observations_history[i][key])
    return data
