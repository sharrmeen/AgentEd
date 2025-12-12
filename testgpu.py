#ONLY FOR NVIDIA GPU
# You may need to adjust the CUDA version based on what is installed on your PC.  
# pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118  #Change thenversion here eg cu130

import torch
print(f"CUDA available: {torch.cuda.is_available()}")
print(f"GPU Name: {torch.cuda.get_device_name(0)}" if torch.cuda.is_available() else "GPU not found.")