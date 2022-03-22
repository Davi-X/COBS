from utils.ActionCreator import ActionCreator
SatAction = ActionCreator("Schedule:Compact", "Schedule Value", "SEASONAL-RESET-SUPPLY-AIR-TEMP-SCH")
SatAction1 = ActionCreator("System Node Setpoint", "Temperature Setpoint", "VAV_1_OA-VAV_1_CoolCNode")
SatAction2 = ActionCreator("System Node Setpoint", "Temperature Setpoint", "VAV_2_OA-VAV_2_CoolCNode")
SatAction3 = ActionCreator("System Node Setpoint", "Temperature Setpoint", "VAV_3_OA-VAV_3_CoolCNode")

zones = ['Core_bottom', 'Core_mid', 'Core_top',
         'Perimeter_bot_ZN_1', 'Perimeter_bot_ZN_2', 'Perimeter_bot_ZN_3', 'Perimeter_bot_ZN_4',
         'Perimeter_mid_ZN_1', 'Perimeter_mid_ZN_2', 'Perimeter_mid_ZN_3', 'Perimeter_mid_ZN_4',
         'Perimeter_top_ZN_1', 'Perimeter_top_ZN_2', 'Perimeter_top_ZN_3', 'Perimeter_top_ZN_4']

# No disturbances as they are normalized by the previous epoch data and pass to 'vectorise()' method as a parameter
# dist_names = [ 'Outdoor RH', 'Wind Speed', 'Wind Direction', 'Direct Solar Rad.', 'Diffuse Solar Rad.',
#               'Ambient Temp.']
state_names = ['time', {'temperature': zones}]

disturbances_dict = {"Site Outdoor Air Drybulb Temperature": "Ambient Temp.",
                     "Site Outdoor Air Relative Humidity": "Outdoor RH",
                     "Site Wind Speed": "Wind Speed",
                     "Site Wind Direction": "Wind Direction",
                     "Site Diffuse Solar Radiation Rate per Area": "Diffuse Solar Rad.",
                     "Site Direct Solar Radiation Rate per Area": "Direct Solar Rad."}

eplus_naming_dict = {
    # Environmental Disturbances
    ('Site Outdoor Air Drybulb Temperature', '*'): "Ambient Temp.",
    ('Site Outdoor Air Relative Humidity', '*'): "Outdoor RH",
    ('Site Diffuse Solar Radiation Rate per Area', '*'): "Diffuse Solar Rad.",
    ('Site Direct Solar Radiation Rate per Area', '*'): "Direct Solar Rad.",
    ('Site Wind Speed', '*'): "Wind Speed",
    ('Site Wind Direction', '*'): "Wind Direction",
    # These are for Large Office reference building
    # ('Chiller Electric Energy', 'COOLSYS1 CHILLER 1'): "Chiller 1 Electricity",
    # ('Chiller Electric Energy', 'COOLSYS1 CHILLER 2'): "Chiller 2 Electricity",
    #
    # ('Facility Total HVAC Electric Demand Power', '*'): "All AHUs'Fan Power",
    #
    # ('Cooling Tower Fan Electric Energy', 'TOWERWATERSYS COOLTOWER'): 'Cool Tower Fan Electricity',
    # ('Pump Electric Energy', 'COOLSYS1 PUMP'): 'CoolSys Pump Electricity',
    # ('Pump Electric Energy', 'HEATSYS1 PUMP'): 'HeatSys Pump Electricity',
    # ('Pump Electric Energy', 'SWHSYS1 PUMP'): 'Water Heating Pump Electricity',
    # ('Pump Electric Energy', 'TOWERWATERSYS PUMP'): 'Water Tower Pump Electricity',

    # ('Boiler Ancillary Electric Energy', 'HEATSYS1 BOILER'): "Boiler Cost",
    # ('Heating Coil Heating Energy', '*'): "Heating Cost",
    # ('Cooling Coil Total Cooling Energy', '*'): "Cooling Cost",
    # ('Chiller Electric Energy', 'COOLSYS1 CHILLER 1'): "Chiller 1 Electricity",
    # ('Chiller Electric Energy', 'COOLSYS1 CHILLER 2'): "Chiller 2 Electricity",

    ('Facility Total HVAC Electric Demand Power', '*'): "HVAC Power",

    # Mixed Air
    ('System Node Temperature', 'VAV_1_OA-VAV_1_CoolCNode'): "VAV1 MA Temp.",
    ('System Node Temperature', 'VAV_2_OA-VAV_2_CoolCNode'): "VAV2 MA Temp.",
    ('System Node Temperature', 'VAV_3_OA-VAV_3_CoolCNode'): "VAV3 MA Temp.",
    # ('System Node Temperature', 'VAV_5_OA-VAV_5_CoolCNode'): "VAV5 MA Temp.",
    ## ('Indoor Air Temperature Setpoint', '*'): "Indoor Temp. Setpoint",

    # Damper
    # ("Zone Air Terminal VAV Damper Position", "BASEMENT VAV BOX COMPONENT"): "Basement VAV Damper Position",
    # ("Zone Air Terminal VAV Damper Position", "CORE_BOTTOM VAV BOX COMPONENT"): "Core_bottom VAV Damper Position",
    # ("Zone Air Terminal VAV Damper Position", "CORE_MID VAV BOX COMPONENT"): "Core_mid VAV Damper Position",
    # ("Zone Air Terminal VAV Damper Position", "CORE_TOP VAV BOX COMPONENT"): "Core_top VAV Damper Position",
    # ("Zone Air Terminal VAV Damper Position", "PERIMETER_BOT_ZN_1 VAV BOX COMPONENT"): "Perimeter_bot_zn_1 VAV Damper Position",
    # ("Zone Air Terminal VAV Damper Position", "PERIMETER_BOT_ZN_2 VAV BOX COMPONENT"): "Perimeter_bot_zn_2 VAV Damper Position",
    # ("Zone Air Terminal VAV Damper Position", "PERIMETER_BOT_ZN_3 VAV BOX COMPONENT"): "Perimeter_bot_zn_3 VAV Damper Position",
    # ("Zone Air Terminal VAV Damper Position", "PERIMETER_BOT_ZN_4 VAV BOX COMPONENT"): "Perimeter_bot_zn_4 VAV Damper Position",
    # ("Zone Air Terminal VAV Damper Position", "PERIMETER_MID_ZN_1 VAV BOX COMPONENT"): "Perimeter_mid_zn_1 VAV Damper Position",
    # ("Zone Air Terminal VAV Damper Position", "PERIMETER_MID_ZN_2 VAV BOX COMPONENT"): "Perimeter_mid_zn_2 VAV Damper Position",
    # ("Zone Air Terminal VAV Damper Position", "PERIMETER_MID_ZN_3 VAV BOX COMPONENT"): "Perimeter_mid_zn_3 VAV Damper Position",
    # ("Zone Air Terminal VAV Damper Position", "PERIMETER_MID_ZN_4 VAV BOX COMPONENT"): "Perimeter_mid_zn_4 VAV Damper Position",
    # ("Zone Air Terminal VAV Damper Position", "PERIMETER_TOP_ZN_1 VAV BOX COMPONENT"): "Perimeter_top_zn_1 VAV Damper Position",
    # ("Zone Air Terminal VAV Damper Position", "PERIMETER_TOP_ZN_2 VAV BOX COMPONENT"): "Perimeter_top_zn_2 VAV Damper Position",
    # ("Zone Air Terminal VAV Damper Position", "PERIMETER_TOP_ZN_3 VAV BOX COMPONENT"): "Perimeter_top_zn_3 VAV Damper Position",
    # ("Zone Air Terminal VAV Damper Position", "PERIMETER_TOP_ZN_4 VAV BOX COMPONENT"): "Perimeter_top_zn_4 VAV Damper Position",
}

eplus_var_types = {
    'Site Outdoor Air Drybulb Temperature': "Environment",
    'Site Outdoor Air Relative Humidity': 'Environment',
    'Site Diffuse Solar Radiation Rate per Area': "Environment",
    'Site Direct Solar Radiation Rate per Area': "Environment",
    'Site Wind Speed': "Environment",
    'Site Wind Direction': 'Environment',
    'Facility Total HVAC Electric Demand Power': 'Whole Building',
    # 'Building Mean Temperature': "EMS",
    # 'Building Mean PPD': "EMS",
    # 'Indoor Air Temperature Setpoint': "EMS",
    # 'Occupancy Flag': "EMS",
}

