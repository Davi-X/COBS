def get_data_from_history(observations_history, key):
    data = []
    for i in range(len(observations_history)):
        data.append(observations_history[i][key])
    return data


def normalize(state, observations_history):
    input_features = ['timestep', 'temperature', 'Ambient Temp.', 'Diff. solar', 'Direct solar']

    normalized_inputs = list()

    for feature in input_features:
        past = get_data_from_history(observations_history, feature)
        # print(feature, past)
        if type(state[feature]) != dict:
            if max(past) - min(past) == 0:
                normalized_inputs.append(0)
                continue
            normalized_inputs.append((state[feature] - min(past)) / (max(past) - min(past)))

        else:
            # change past format if it is a "list of dict" to a "dict of list"
            zones = state[feature].keys()
            past_dict = {zone: list() for zone in zones}
            for i in range(len(past)):
                for zone in zones:
                    past_dict[zone].append(past[i][zone])
            # print(past_dict)
            normalised_dict = dict()
            for zone, value in state[feature].items():
                if max(past_dict[zone]) - min(past_dict[zone]) == 0:
                    normalised_dict[zone] = 0
                    continue
                normalised_dict[zone] = (value - min(past_dict[zone])) / (max(past_dict[zone]) - min(past_dict[zone]))
            normalized_inputs.append(normalised_dict)

    return normalized_inputs
