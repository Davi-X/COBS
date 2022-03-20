import os
import torch as T
import torch.nn as nn
import torch.optim as optim
import torch.nn.functional as F


def weights_init_(m):
    if isinstance(m, nn.Linear):
        T.nn.init.xavier_uniform_(m.weight, 1)
        T.nn.init.constant_(m.bias, 0)
        for m in m.modules():
            print(m)


class DQN_Network(nn.Module):

    def __init__(self, lr, num_features, num_actions, chkpt_dir):
        if not os.path.exists(chkpt_dir):
            os.makedirs(chkpt_dir)
        self.chkpt_dir = chkpt_dir

        super(DQN_Network, self).__init__()
        self.fc1 = nn.Linear(num_features, 50)
        self.fc2 = nn.Linear(50, 100)
        self.fc3 = nn.Linear(100, 200)
        self.out = nn.Linear(200, num_actions)

        self.apply(weights_init_)
        self.optimizer = optim.RMSprop(self.parameters(), lr)
        self.loss = nn.MSELoss()
        self.device = T.device('cuda:0' if T.cuda.is_available() else 'cpu')
        self.to(self.device)

    def forward(self, t):
        t = F.relu(self.fc1(t))
        t = F.relu(self.fc2(t))
        t = F.relu(self.fc3(t))
        return self.out(t)

    def save_checkpoint(self, num):
        checkpoint_file = os.path.join(self.chkpt_dir, self.name + f'_{num}')
        print('... saving checkpoint ...')
        T.save(self.state_dict(), checkpoint_file)

    def load_checkpoint(self, num):
        checkpoint_file = os.path.join(self.chkpt_dir, self.name + f'_{num}')
        print('... loading checkpoint ...')
        self.load_state_dict(T.load(checkpoint_file))
