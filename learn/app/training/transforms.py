"""PyTorch transforms for data augmentation"""

from torchvision import transforms


def create_train_transforms(config: dict) -> transforms.Compose:
    """Create training transforms based on augmentation config."""
    preprocessing = config.get("preprocessing", {})
    augmentation = config.get("augmentation", {})

    target_size = preprocessing.get("target_size", (224, 224))
    normalization = preprocessing.get("normalization", "[0,1]")
    color_mode = preprocessing.get("color_mode", "RGB")

    transform_list = []

    # Resize
    transform_list.append(transforms.Resize(target_size))

    # Convert grayscale to RGB if needed (most pretrained models expect RGB)
    if color_mode == "Grayscale":
        transform_list.append(transforms.Grayscale(num_output_channels=3))

    # Augmentation transforms
    preset = augmentation.get("preset", "None")
    custom = augmentation.get("custom", {})

    if preset == "Light":
        transform_list.extend([
            transforms.RandomHorizontalFlip(p=0.5),
            transforms.RandomChoice([
                transforms.RandomRotation([0, 0]),
                transforms.RandomRotation([90, 90]),
                transforms.RandomRotation([180, 180]),
                transforms.RandomRotation([270, 270]),
            ]),
        ])
    elif preset == "Moderate":
        transform_list.extend([
            transforms.RandomHorizontalFlip(p=0.5),
            transforms.RandomVerticalFlip(p=0.5),
            transforms.RandomChoice([
                transforms.RandomRotation([0, 0]),
                transforms.RandomRotation([90, 90]),
                transforms.RandomRotation([180, 180]),
                transforms.RandomRotation([270, 270]),
            ]),
            transforms.ColorJitter(brightness=0.1, contrast=0.1),
        ])
    elif preset == "Heavy":
        transform_list.extend([
            transforms.RandomHorizontalFlip(p=0.5),
            transforms.RandomVerticalFlip(p=0.5),
            transforms.RandomChoice([
                transforms.RandomRotation([0, 0]),
                transforms.RandomRotation([90, 90]),
                transforms.RandomRotation([180, 180]),
                transforms.RandomRotation([270, 270]),
            ]),
            transforms.ColorJitter(brightness=0.2, contrast=0.2),
            transforms.GaussianBlur(kernel_size=3, sigma=(0.1, 0.5)),
        ])
    elif preset == "Custom":
        if custom.get("horizontal_flip"):
            transform_list.append(transforms.RandomHorizontalFlip(p=0.5))
        if custom.get("vertical_flip"):
            transform_list.append(transforms.RandomVerticalFlip(p=0.5))
        if custom.get("rotation"):
            angles = custom.get("rotation_angles", [90, 180, 270])
            rotation_choices = [transforms.RandomRotation([a, a]) for a in angles]
            rotation_choices.insert(0, transforms.RandomRotation([0, 0]))
            transform_list.append(transforms.RandomChoice(rotation_choices))
        brightness = custom.get("brightness_range", 0) / 100.0
        contrast = custom.get("contrast_range", 0) / 100.0
        if brightness > 0 or contrast > 0:
            transform_list.append(transforms.ColorJitter(brightness=brightness, contrast=contrast))
        if custom.get("gaussian_noise"):
            transform_list.append(transforms.GaussianBlur(kernel_size=3, sigma=(0.1, 0.5)))

    # Convert to tensor
    transform_list.append(transforms.ToTensor())

    # Normalization
    if normalization == "[-1,1]":
        transform_list.append(transforms.Normalize(mean=[0.5, 0.5, 0.5], std=[0.5, 0.5, 0.5]))
    elif normalization == "ImageNet Mean/Std":
        transform_list.append(transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]))
    # "[0,1]" is default after ToTensor(), no additional normalization needed

    return transforms.Compose(transform_list)


def create_val_transforms(config: dict) -> transforms.Compose:
    """Create validation/test transforms (no augmentation)."""
    preprocessing = config.get("preprocessing", {})

    target_size = preprocessing.get("target_size", (224, 224))
    normalization = preprocessing.get("normalization", "[0,1]")
    color_mode = preprocessing.get("color_mode", "RGB")

    transform_list = [transforms.Resize(target_size)]

    if color_mode == "Grayscale":
        transform_list.append(transforms.Grayscale(num_output_channels=3))

    transform_list.append(transforms.ToTensor())

    if normalization == "[-1,1]":
        transform_list.append(transforms.Normalize(mean=[0.5, 0.5, 0.5], std=[0.5, 0.5, 0.5]))
    elif normalization == "ImageNet Mean/Std":
        transform_list.append(transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]))

    return transforms.Compose(transform_list)
