import torch.nn as nn
from torchvision.models.resnet import resnet50
from torchvision.models.vgg import vgg16

import dino.vision_transformer as vits
from dino import utils


def get_model(arch, patch_size, resnet_dilate, device, pretrained_weights, key):
    if "resnet" in arch:
        if resnet_dilate == 1:
            replace_stride_with_dilation = [False, False, False]
        elif resnet_dilate == 2:
            replace_stride_with_dilation = [False, False, True]
        elif resnet_dilate == 4:
            replace_stride_with_dilation = [False, True, True]

        if "imagenet" in arch:
            model = resnet50(
                pretrained=True,
                replace_stride_with_dilation=replace_stride_with_dilation,
            )
        else:
            model = resnet50(
                pretrained=False,
                replace_stride_with_dilation=replace_stride_with_dilation,
            )
    elif "vgg16" in arch:
        if "imagenet" in arch:
            model = vgg16(pretrained=True)
        else:
            model = vgg16(pretrained=False)
    else:
        model = vits.__dict__[arch](patch_size=patch_size, num_classes=0)

    for p in model.parameters():
        p.requires_grad = False

    # Initialize model with pretraining
    if "imagenet" not in arch:
        # url = None
        # if arch == "vit_small" and patch_size == 16:
            # url = "dino_deitsmall16_pretrain/dino_deitsmall16_pretrain.pth"
        # elif arch == "vit_small" and patch_size == 8:
            # url = "dino_deitsmall8_300ep_pretrain/dino_deitsmall8_300ep_pretrain.pth"  # model used for visualizations in our paper
        # elif arch == "vit_base" and patch_size == 16:
            # url = "dino_vitbase16_pretrain/dino_vitbase16_pretrain.pth"
        # elif arch == "vit_base" and patch_size == 8:
            # url = "dino_vitbase8_pretrain/dino_vitbase8_pretrain.pth"
        # elif arch == "resnet50":
            # url = "dino_resnet50_pretrain/dino_resnet50_pretrain.pth"
        model.cuda()
        prefix = None
        key_ = "model"
        if any(s in pretrained_weights for s in ['soco', 'pixpro']):
            prefix = "module.encoder."
        elif "mae" not in pretrained_weights:
            if 'student' in key:
                prefix = "module.backbone."
            else:
                prefix = "backbone."
            key_ = key

        if "resnet" in arch:
            model = ResNet50Bottom(model)
        elif "vgg16" in arch:
            model = vgg16Bottom(model)
        utils.load_pretrained_weights(model, pretrained_weights, key_, prefix)

    # If ResNet or VGG16 loose the last fully connected layer
    if "resnet" in arch:
        model = ResNet50Bottom(model)
    elif "vgg16" in arch:
        model = vgg16Bottom(model)

    model.eval()
    return model


class ResNet50Bottom(nn.Module):
    # https://forums.fast.ai/t/pytorch-best-way-to-get-at-intermediate-layers-in-vgg-and-resnet/5707/2
    def __init__(self, original_model):
        super(ResNet50Bottom, self).__init__()
        # Remove avgpool and fc layers
        self.features = nn.Sequential(*list(original_model.children())[:-2])

    def forward(self, x):
        x = self.features(x)
        return x


class vgg16Bottom(nn.Module):
    # https://forums.fast.ai/t/pytorch-best-way-to-get-at-intermediate-layers-in-vgg-and-resnet/5707/2
    def __init__(self, original_model):
        super(vgg16Bottom, self).__init__()
        # Remove avgpool and the classifier
        self.features = nn.Sequential(*list(original_model.children())[:-2])
        # Remove the last maxPool2d
        self.features = nn.Sequential(*list(self.features[0][:-1]))

    def forward(self, x):
        x = self.features(x)
        return x
