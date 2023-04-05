import logging
import os
import sys
import warnings

logging.basicConfig(level=logging.ERROR)
warnings.filterwarnings("ignore", message="Failed to load image Python extension*")
os.environ["TOKENIZERS_PARALLELISM"] = "0"

import intel_extension_for_pytorch  # add xpu name space when torch is imported
