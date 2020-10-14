import os, random, pickle
import numpy as np


class ReplayBuffer:
    def __init__(self,
                 capacity=None,
                 seed=None,
                 chkpt_dir=None):
        if chkpt_dir is not None and not os.path.exists(chkpt_dir):
            os.makedirs(chkpt_dir)
        self.chkpt_dir = chkpt_dir
        if seed is not None:
            random.seed(seed)
        self.capacity = capacity
        self.buffer = []
        self.position = 0
        self.ignore_set = set()
        self.save_set = set()

    def push(self, prev_state, prev_action, current_state):
        if self.capacity is None or len(self.buffer) < self.capacity:
            self.buffer.append(None)

        if len(self.save_set) == 0:
            self.save_set = set(current_state.keys()) - self.ignore_set

        prev_state = {key: prev_state[key] for key in self.save_set}
        current_state = {key: current_state[key] for key in self.save_set}

        self.buffer[self.position] = (prev_state, prev_action, current_state, False)
        self.position += 1
        if self.capacity:
            self.position %= self.capacity

    def sample(self, batch_size):
        batch = random.sample(self.buffer, batch_size)
        state, action, next_state, done = map(np.stack, zip(*batch))
        return state, action, next_state, done

    def save(self, num):
        checkpoint_file = os.path.join(self.chkpt_dir, f'memory_{num}')
        dump_dict = {
            'capacity': self.capacity,
            'buffer': self.buffer,
            'position': self.position
        }
        with open(checkpoint_file, "wb") as f:
            pickle.dump(dump_dict, f)

    def load(self, num):
        checkpoint_file = os.path.join(self.chkpt_dir, f'memory_{num}')
        with open(checkpoint_file, "rb") as f:
            dump_dict = pickle.load(f)
            self.capacity = dump_dict['capacity']
            self.buffer = dump_dict['buffer']
            self.position = dump_dict['position']

    def __len__(self):
        return len(self.buffer)

    def reset(self):
        self.buffer = list()
        self.position = 0
        self.save_set = set()
        self.ignore_set = set()

    def terminate(self):
        prev_buffer = list(self.buffer[self.position - 1])
        prev_buffer[3] = True
        self.buffer[self.position - 1] = tuple(prev_buffer)

    def set_ignore(self, ignore_set):
        self.ignore_set = ignore_set
