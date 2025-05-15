# services/ai_utils.py

import torch
from PIL import Image
from torchvision import transforms
from transformers import BlipProcessor, BlipForConditionalGeneration, CLIPProcessor, CLIPModel
import os
from schemas.ai_validation import ClassificationResult , DescriptionResult
# Initialize once for performance
clip_model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32")
clip_processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")

blip_processor = BlipProcessor.from_pretrained("Salesforce/blip-image-captioning-base")
blip_model = BlipForConditionalGeneration.from_pretrained("Salesforce/blip-image-captioning-base")

# Device configuration
device = "cuda" if torch.cuda.is_available() else "cpu"
clip_model.to(device)
blip_model.to(device)

CATEGORIES = [
    "portrait", "landscape", "wildlife", "architecture", "food", 
    "sports", "fashion", "travel", "macro", "abstract"
]

def classify_image(image_path: str) -> str:
    image = Image.open(image_path).convert("RGB")
    inputs = clip_processor(text=CATEGORIES, images=image, return_tensors="pt", padding=True).to(device)

    outputs = clip_model(**inputs)
    logits_per_image = outputs.logits_per_image
    probs = logits_per_image.softmax(dim=1)

    predicted_index = torch.argmax(probs, dim=1).item()
    validated_category = ClassificationResult(category=CATEGORIES[predicted_index])
    return validated_category

def describe_image(image_path: str) -> str:
    image = Image.open(image_path).convert("RGB")
    inputs = blip_processor(image, return_tensors="pt").to(device)
    out = blip_model.generate(**inputs)
    description = blip_processor.decode(out[0], skip_special_tokens=True)
    validated_description = DescriptionResult(description=description)
    return validated_description
