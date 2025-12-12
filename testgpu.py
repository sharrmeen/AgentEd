import torch
print(f"CUDA available: {torch.cuda.is_available()}")
print(f"GPU Name: {torch.cuda.get_device_name(0)}" if torch.cuda.is_available() else "GPU not found.")