import torch.optim as optim
import torch.nn as nn
import torch.nn.functional as F
import torch


import torch
import torch.nn as nn
import torch.nn.functional as F


class DQNAtari(nn.Module):
    def __init__(self, input_channel_size: int, output_size: int):
        super(DQNAtari, self).__init__()
        self.conv1 = nn.Conv2d(input_channel_size, 32, kernel_size=8, stride=4)
        self.conv2 = nn.Conv2d(32, 64, kernel_size=4, stride=2)
        self.conv3 = nn.Conv2d(64, 64, kernel_size=3, stride=1)
        self.fc = nn.Linear(3136, 512)
        self.fc_2 = nn.Linear(512, output_size)

    def forward(self, x):
        x = self.conv1(x)
        x = F.relu(x)  # self.bn1(x))
        x = self.conv2(x)
        x = F.relu(x)  # self.bn2(x))
        x = self.conv3(x)
        x = F.relu(x)  # self.bn3(x))
        x = x.view(-1, 3136)
        x = self.fc(x)
        x = F.relu(x)
        x = self.fc_2(x)
        return x


class DoubleDQNAtari(DQNAtari):
    def __init__(self, input_channel_size: int, output_size: int):
        super(DoubleDQNAtari, self).__init__(input_channel_size, output_size)
        self.fc_2 = nn.Linear(512, output_size, bias=False)
        self.shared_bias = nn.Parameter(torch.zeros(1))

    def forward(self, x):
        x = super(DoubleDQNAtari, self).forward(x)
        return x + self.shared_bias


# advanced network
class DuelingDQNAtari(DQNAtari):
    def __init__(self, input_channel_size: int, output_size: int):
        super(DuelingDQNAtari, self).__init__(input_channel_size, output_size)
        # for advanced output
        self.fc = nn.Linear(3136, 512)
        self.fc_2 = nn.Linear(512, output_size)
        self.fc_3 = nn.Linear(512, 1)

    def _register_gradient_rescale(self):
        """Rescales the gradients entering the last convolutional layer by 1/sqrt(2)."""

        def rescale_gradients(grad):
            return grad / (2 ** 0.5)

        # Attach the hook to the last convolutional layer
        self.conv3.weight.register_hook(rescale_gradients)
        self.conv3.bias.register_hook(rescale_gradients)

    def forward(self, x):
        x = self.conv1(x)
        x = F.relu(x)  # self.bn1(x))
        x = self.conv2(x)
        x = F.relu(x)  # self.bn2(x))
        x = self.conv3(x)
        x = F.relu(x)  # self.bn3(x))
        x = x.view(-1, 3136)
        x = self.fc(x)
        features = F.relu(x)
        a_values = self.fc_2(features)
        s_values = self.fc_3(features)
        hat_s = a_values.mean(dim=1, keepdim=True)
        return a_values - hat_s + s_values
