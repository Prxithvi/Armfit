import torch
import torch.nn as nn

class TinyCNN(nn.Module):
    def __init__(self):
        super().__init__()
        self.net = nn.Sequential(
            nn.Conv2d(3, 8, 3, padding=1),
            nn.ReLU(),
            nn.Conv2d(8, 16, 3, padding=1),
            nn.ReLU(),
            nn.AdaptiveAvgPool2d((1,1)),
            nn.Flatten(),
            nn.Linear(16, 10),
        )

    def forward(self, x):
        return self.net(x)

model = TinyCNN().eval()
example = (torch.randn(1, 3, 224, 224),)

from executorch.exir import to_edge

edge = to_edge(torch.export.export(model, example))
program = edge.to_executorch()

with open("tinycnn.pte", "wb") as f:
    program.write_to_file(f)

print("Created tinycnn.pte")