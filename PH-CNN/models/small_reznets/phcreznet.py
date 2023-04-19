import torch
import torch.nn as nn
import torch.nn.functional as F
import torch.nn.init as init

from models.ph_layers.hypercomplex_layers import PHConv

__all__ = ['ResNet', 'resnet20', 'resnet32', 'resnet44', 'resnet56', 'resnet110', 'resnet1202']

def _weights_init(m):
    classname = m.__class__.__name__
    #print(classname)
    if isinstance(m, nn.Linear):
        init.kaiming_normal_(m.weight)

class LambdaLayer(nn.Module):
    def __init__(self, lambd):
        super(LambdaLayer, self).__init__()
        self.lambd = lambd

    def forward(self, x):
        return self.lambd(x)


class BasicBlock(nn.Module):
    expansion = 1

    def __init__(self, in_planes, planes, stride=1, option='B', n=4, rezero=True):
        super(BasicBlock, self).__init__()
        self.conv1 = PHConv(n, in_planes, planes, kernel_size=3, stride=stride, padding=1)
        self.bn1 = nn.BatchNorm2d(planes)
        self.conv2 = PHConv(n, planes, planes, kernel_size=3, stride=1, padding=1)
        self.bn2 = nn.BatchNorm2d(planes)

        self.shortcut = nn.Sequential()
        if stride != 1 or in_planes != planes:
            if option == 'A':
                """
                For CIFAR10 ResNet paper uses option A.
                """
                self.shortcut = LambdaLayer(lambda x:
                                            F.pad(x[:, :, ::2, ::2], (0, 0, 0, 0, planes//4, planes//4), "constant", 0))
            elif option == 'B':
                self.shortcut = nn.Sequential(
                     PHConv(n, in_planes, self.expansion * planes, kernel_size=1, stride=stride),
                     nn.BatchNorm2d(self.expansion * planes)
                )
        
        self.rezero = rezero
        if self.rezero:
            self.res_weight = nn.Parameter(torch.zeros(1), requires_grad=True)

    def forward(self, x):
        out = F.relu(self.bn1(self.conv1(x)))
        out = self.bn2(self.conv2(out))

        if self.rezero:
            out = self.shortcut(x) + self.res_weight * F.relu(out)
        else:
            out = F.relu(self.shortcut(x) + out)
    
        return out


class PHMResNet(nn.Module):
    def __init__(self, block, num_blocks, num_classes=10, channels=3, n=1, rezero=False):
        super(PHMResNet, self).__init__()
        self.in_planes = 16

        self.conv1 = PHConv(n, channels, 16, kernel_size=3, stride=1, padding=1)
        self.bn1 = nn.BatchNorm2d(16)
        self.layer1 = self._make_layer(block, 16, num_blocks[0], stride=1, n=n, rezero=rezero)
        self.layer2 = self._make_layer(block, 32, num_blocks[1], stride=2, n=n, rezero=rezero)
        self.layer3 = self._make_layer(block, 64, num_blocks[2], stride=2, n=n, rezero=rezero)
        self.linear = nn.Linear(64, num_classes)

        self.apply(_weights_init)

    def _make_layer(self, block, planes, num_blocks, stride, n, rezero=False):
        strides = [stride] + [1]*(num_blocks-1)
        layers = []
        for stride in strides:
            layers.append(block(self.in_planes, planes, stride, n=n, rezero=rezero))
            self.in_planes = planes * block.expansion

        return nn.Sequential(*layers)

    def forward(self, x):
        out = F.relu(self.bn1(self.conv1(x)))
        out = self.layer1(out)
        out = self.layer2(out)
        out = self.layer3(out)
        out = F.avg_pool2d(out, out.size()[3])
        out = out.view(out.size(0), -1)
        out = self.linear(out)
        return out


class PHMResNetLarge(nn.Module):
    def __init__(self, block, num_blocks, num_classes=10, channels=3, n=1, rezero=False):
        super(PHMResNetLarge, self).__init__()
        self.in_planes = 24

        self.conv1 = PHConv(n, channels, 24, kernel_size=3, stride=1, padding=1)
        self.bn1 = nn.BatchNorm2d(24)
        self.layer1 = self._make_layer(block, 24, num_blocks[0], stride=1, n=n, rezero=rezero)
        self.layer2 = self._make_layer(block, 72, num_blocks[1], stride=2, n=n, rezero=rezero)
        self.layer3 = self._make_layer(block, 216, num_blocks[2], stride=2, n=n, rezero=rezero)
        self.linear = nn.Linear(216, num_classes)

        self.apply(_weights_init)

    def _make_layer(self, block, planes, num_blocks, stride, n, rezero=False):
        strides = [stride] + [1]*(num_blocks-1)
        layers = []
        for stride in strides:
            layers.append(block(self.in_planes, planes, stride, n=n, rezero=rezero))
            self.in_planes = planes * block.expansion

        return nn.Sequential(*layers)

    def forward(self, x):
        out = F.relu(self.bn1(self.conv1(x)))
        out = self.layer1(out)
        out = self.layer2(out)
        out = self.layer3(out)
        out = F.avg_pool2d(out, out.size()[3])
        out = out.view(out.size(0), -1)
        out = self.linear(out)
        return out


def phcresnet20(channels=4, n=4, num_classes=10, rezero=False):
    return PHMResNet(BasicBlock, [3, 3, 3], channels=channels, n=n, num_classes=num_classes, rezero=rezero)

def phcresnet20large(channels=4, n=4, num_classes=10, rezero=False):
    return PHMResNetLarge(BasicBlock, [3, 3, 3], channels=channels, n=n, num_classes=num_classes, rezero=rezero)


def phcresnet32(channels=4, n=4, num_classes=10, rezero=False):
    return PHMResNet(BasicBlock, [5, 5, 5], channels=channels, n=n, num_classes=num_classes, rezero=rezero)


def phcresnet44(channels=4, n=4, num_classes=10, rezero=False):
    return PHMResNet(BasicBlock, [7, 7, 7], channels=channels, n=n, num_classes=num_classes, rezero=rezero)


def phcresnet56(channels=4, n=4, num_classes=10, rezero=False):
    return PHMResNet(BasicBlock, [9, 9, 9], channels=channels, n=n, num_classes=num_classes, rezero=rezero)


def phcresnet110(channels=4, n=4, num_classes=10, rezero=False):
    return PHMResNet(BasicBlock, [18, 18, 18], channels=channels, n=n, num_classes=num_classes, rezero=rezero)

def phcresnet110large(channels=4, n=4, num_classes=10, rezero=False):
    return PHMResNetLarge(BasicBlock, [18, 18, 18], channels=channels, n=n, num_classes=num_classes, rezero=rezero)


def phcresnet1202(channels=4, n=4, num_classes=10, rezero=False):
    return PHMResNet(BasicBlock, [200, 200, 200], channels=channels, n=n, num_classes=num_classes, rezero=rezero)
