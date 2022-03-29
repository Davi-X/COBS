import pdb

import numpy as np
import torch as T

from agents.ReplayMemory import ReplayMemory
from utils.agent import augment_ma


class BDDQNAgent():

    def __init__(self, agent_info, Network, chkpt_dir='.'):

        # super(BDDQNAgent, self).__init__(agent_info, Network, chkpt_dir=chkpt_dir)

        self.type = 'DDQNAgent'
        # Set Hyperparameters
        self.gamma = agent_info.get('gamma')
        self.epsilon = agent_info.get('epsilon')
        self.lr = agent_info.get('lr')
        self.input_dims = agent_info.get('input_dims')
        self.batch_size = agent_info.get('batch_size')
        self.eps_min = agent_info.get('eps_min')
        self.eps_dec = agent_info.get('eps_dec')
        self.replace_target_cnt = agent_info.get('replace')

        # Discrete num actions
        self.num_sat_actions = agent_info.get('num_actions', 0)

        # Num AHUs
        self.num_sat_action_zones = agent_info.get('num_action_zones', 0)

        self.stpt_action_space = np.linspace(
                agent_info.get('min_sat_action'), agent_info.get('max_sat_action'), self.num_sat_actions).round(1)
        # self.therm_action_space = np.linspace( agent_info.get('min_therm_action', 0), agent_info.get(
        # 'max_therm_action', 40), self.discrete_therm_actions).round()

        self.chkpt_dir = chkpt_dir
        self.learn_step_counter = 0

        self.memory = ReplayMemory(
            agent_info.get('mem_size'),
            agent_info.get('seed'),
            chkpt_dir
        )

        self.q_eval = Network(self.lr, self.input_dims[0], self.num_sat_action_zones, self.num_sat_actions, self.chkpt_dir).double()

        self.q_next = Network(self.lr, self.input_dims[0], self.num_sat_action_zones, self.num_sat_actions, self.chkpt_dir).double()

    def choose_action(self, observation):
        if np.random.random() > self.epsilon:
            state, _, _ = observation
            _, a_stpts = self.q_eval.forward(T.tensor(state).double())
            stpt_actions = []
            therm_actions = []
            blind_actions = []
            idxs = []

            for a in a_stpts:
                actions_stpt_idx = T.argmax(a).item()
                stpt_actions.append(self.stpt_action_space[actions_stpt_idx])
                idxs.append(actions_stpt_idx)
            # for a in a_therms:
            #     actions_stpt_idx = T.argmax(a).item()
            #     therm_actions.append(self.therm_action_space[actions_stpt_idx])
            #     idxs.append(actions_stpt_idx)

        else:
            stpt_actions = []
            therm_actions = []
            blind_actions = []
            idxs = []

            for i in range(0, self.num_sat_action_zones):
                rand = np.random.choice(self.stpt_action_space)
                stpt_actions.append(rand)
                idxs.append(np.where(self.stpt_action_space == rand)[0].item())
            # for i in range(0, self.num_therm_actions):
            #     rand = np.random.choice(self.therm_action_space)
            #     therm_actions.append(rand)
            #     idxs.append(np.where(self.therm_action_space == rand)[0].item())

        sat_actions_tups = []
        for i in range(len(stpt_actions)):
            action_stpt, sat_sp = augment_ma(observation, stpt_actions[i])
            sat_actions_tups.append((action_stpt, sat_sp[i]))
        return sat_actions_tups, idxs

    def store_transition(self, observation, action, reward, observation_, done):
        # TODO - need to test that the action index is working properly
        _, action_idxs = action
        state, _, _ = observation
        state_, _, _ = observation_
        self.memory.push(state, action_idxs, reward, state_, done)

    def sample_memory(self):
        state, action, reward, new_state, done = self.memory.sample(batch_size=self.batch_size)

        states = T.tensor(state).to(self.q_eval.device)
        rewards = T.tensor(reward).to(self.q_eval.device)
        actions = T.tensor(action).to(self.q_eval.device)
        dones = T.BoolTensor(done.astype(int)).to(self.q_eval.device)
        states_ = T.tensor(new_state).to(self.q_eval.device)

        return states, actions, rewards, states_, dones

    def replace_target_network(self):
        if self.replace_target_cnt is not None and \
           self.learn_step_counter % self.replace_target_cnt == 0:
            self.q_next.load_state_dict(self.q_eval.state_dict())

    def decrement_epsilon(self):
        self.epsilon = self.epsilon - self.eps_dec \
            if self.epsilon > self.eps_min else self.eps_min

    def learn(self):
        if len(self.memory) < self.batch_size:
            return

        self.q_eval.optimizer.zero_grad()

        self.replace_target_network()

        states, actions, rewards, states_, dones = self.sample_memory()
        indices = np.arange(self.batch_size)

        V_s, A_stpts = self.q_eval.forward(states)
        V_s_, A_stpts_ = self.q_next.forward(states_)

        actions = actions.type(T.long)

        losses = []
        act_idx = 0
        for A_s, A_s_ in zip(A_stpts, A_stpts_):
            q_pred = T.add(V_s, (A_s - A_s.mean(dim=1, keepdim=True)))[indices, actions[:, act_idx]].double()
            q_next = T.add(V_s_, (A_s_ - A_s_.mean(dim=1, keepdim=True))).max(dim=1)[0]
            q_target = rewards + self.gamma * q_next.double()
            loss = self.q_eval.loss(q_target, q_pred).to(self.q_eval.device)
            losses.append(loss)
            act_idx += 1

        T.autograd.backward(losses)
        self.q_eval.optimizer.step()
        self.learn_step_counter += 1
        self.decrement_epsilon()

    def agent_start(self, state):
        # action = [(sat_action1, sat_AHU1), (sat_action2, sat_AHU2), (sat_action3, sat_AHU3)], idxs
        action = self.choose_action(state)
        self.last_action = action
        self.last_state = state
        return self.last_action

    def agent_step(self, reward, state):
        # last_action = [(sat_action1, sat_AHU1), (sat_action2, sat_AHU2), (sat_action3, sat_AHU3)], idxs
        self.store_transition(self.last_state, self.last_action, reward, state, False)
        self.learn()
        action = self.choose_action(state)
        self.last_action = action
        self.last_state = state
        return self.last_action

    def save(self, num):
        self.q_eval.save_checkpoint(num)
        self.q_next.save_checkpoint(num)
        self.memory.save(num)

    def load(self, num):
        self.q_eval.load_checkpoint(num)
        self.q_next.load_checkpoint(num)
        self.memory.load(num)