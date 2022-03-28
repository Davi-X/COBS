import os

import torch
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim
import torch as T


# Initialize Policy weights
def weights_init_(m):
    if isinstance(m, nn.Linear):
        torch.nn.init.xavier_uniform_(m.weight, gain=1)
        torch.nn.init.constant_(m.bias, 0)


class BDDQN_Network(nn.Module):
    def __init__(self, lr, input_dims, num_actions_zones, num_actions, chkpt_dir):
        if not os.path.exists(chkpt_dir):
            os.makedirs(chkpt_dir)
        self.chkpt_dir = chkpt_dir

        super(BDDQN_Network, self).__init__()
        # self.to(self.device)

        self.num_actions_zones = num_actions_zones

        # Base Network
        self.linear1 = nn.Linear(input_dims[0], 512).to(self.device)
        self.linear2 = nn.Linear(512, 256).to(self.device)
        self.linear3 = nn.Linear(256, 128).to(self.device)

        # Value estimate
        self.V = nn.Linear(128, 1).to(self.device)

        # Action estimates
        for i in range(num_actions_zones):
            setattr(self, f"A_stpt_{i}", nn.Linear(128, num_actions))

        self.apply(weights_init_)
        self.optimizer = optim.Adam(self.parameters(), lr=lr)
        self.loss = nn.MSELoss()
        self.device = T.device('cuda:0' if T.cuda.is_available() else 'cpu')
        self.to(self.device)

    def forward(self, x):
        x1 = F.relu(self.linear1(x))
        x1 = F.relu(self.linear2(x1))
        x1 = F.relu(self.linear3(x1))

        V = self.V(x1)

        A_stpts = []
        for i in range(self.n_stpt_actions):
            A = getattr(self, f"A_stpt_{i}")
            A_stpts.append(A(x1))

        return V, A_stpts

    def save_checkpoint(self, num):
        checkpoint_file = os.path.join(self.chkpt_dir, self.name + f'_{num}')
        print('... saving checkpoint ...')
        T.save(self.state_dict(), checkpoint_file)

    def load_checkpoint(self, num):
        checkpoint_file = os.path.join(self.chkpt_dir, self.name + f'_{num}')
        print('... loading checkpoint ...')
        self.load_state_dict(T.load(checkpoint_file))

