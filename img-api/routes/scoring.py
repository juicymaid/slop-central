from fastapi import APIRouter, Query, HTTPException
import os
import json
from utils import images_data  # Changed import from main to utils

import torch
import clip
from PIL import Image
import requests
from io import BytesIO

router = APIRouter()


