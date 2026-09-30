"""Product Image Classifier - Custom CNN for BIS product recognition."""

import io
import os
import json
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, Dataset
from torchvision import transforms
from PIL import Image
import timm
import albumentations as A
from albumentations.pytorch import ToTensorV2
import numpy as np
from pathlib import Path
from typing import List, Tuple, Optional, Dict
import logging

logger = logging.getLogger(__name__)

# Product classes mapping to BIS standards
CLASS_TO_STANDARD = {
    "bottle": {
        "standard": "IS 9845 / IS 14534",
        "description": "Plastic bottles/containers (PET, HDPE)",
        "scheme": "ISI Mark (Scheme-I) / QCO",
        "keywords": ["PET", "HDPE", "bottle", "container", "packaged drinking water"]
    },
    "bulb": {
        "standard": "IS 16102 (Part 1/2)",
        "description": "LED lamps and bulbs",
        "scheme": "CRS (Scheme-II) - Compulsory Registration",
        "keywords": ["LED", "lamp", "bulb", "lighting", "self-ballasted"]
    },
    "helmet": {
        "standard": "IS 4151:2015",
        "description": "Protective helmets for two-wheeler riders",
        "scheme": "ISI Mark (Scheme-I) - Mandatory QCO",
        "keywords": ["helmet", "two-wheeler", "protective", "ISI mark"]
    },
    "gold_jewelry": {
        "standard": "IS 1417 / IS 2790",
        "description": "Gold jewellery / Hallmarking",
        "scheme": "Hallmarking (HUID) - Mandatory",
        "keywords": ["gold", "jewellery", "ornament", "hallmark", "HUID", "916", "22K", "18K"]
    },
    "pressure_cooker": {
        "standard": "IS 2347",
        "description": "Domestic pressure cookers",
        "scheme": "ISI Mark (Scheme-I)",
        "keywords": ["pressure cooker", "cooker", "IS 2347", "stainless steel"]
    },
    "other": {
        "standard": "Unknown",
        "description": "Product not recognized",
        "scheme": "Manual classification required",
        "keywords": []
    }
}

CLASS_NAMES = list(CLASS_TO_STANDARD.keys())
NUM_CLASSES = len(CLASS_NAMES)

# Model paths
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
MODEL_DIR = PROJECT_ROOT / "data" / "models"
MODEL_DIR.mkdir(parents=True, exist_ok=True)
MODEL_PATH = MODEL_DIR / "product_classifier.pth"
LABEL_MAP_PATH = MODEL_DIR / "label_map.json"

# Training data paths
TRAIN_DIR = PROJECT_ROOT / "data" / "train"
VAL_DIR = PROJECT_ROOT / "data" / "val"


class ProductDataset(Dataset):
    """Dataset for product images."""
    
    def __init__(self, root_dir: Path, transform=None, class_to_idx: Optional[Dict] = None):
        self.root_dir = Path(root_dir)
        self.transform = transform
        self.samples = []
        self.class_to_idx = class_to_idx or {cls: i for i, cls in enumerate(CLASS_NAMES)}
        self.idx_to_class = {v: k for k, v in self.class_to_idx.items()}
        
        for class_name in CLASS_NAMES:
            class_dir = self.root_dir / class_name
            if class_dir.exists():
                for img_path in class_dir.glob("*.jpg"):
                    self.samples.append((img_path, self.class_to_idx[class_name]))
                for img_path in class_dir.glob("*.jpeg"):
                    self.samples.append((img_path, self.class_to_idx[class_name]))
                for img_path in class_dir.glob("*.png"):
                    self.samples.append((img_path, self.class_to_idx[class_name]))
        
        logger.info(f"Loaded {len(self.samples)} samples from {root_dir}")
    
    def __len__(self):
        return len(self.samples)
    
    def __getitem__(self, idx):
        img_path, label = self.samples[idx]
        image = Image.open(img_path).convert("RGB")
        image = np.array(image)
        
        if self.transform:
            augmented = self.transform(image=image)
            image = augmented["image"]
        
        return image, label


def get_transforms(train: bool = True, img_size: int = 224):
    """Get albumentations transforms."""
    if train:
        return A.Compose([
            A.Resize(img_size, img_size),
            A.HorizontalFlip(p=0.5),
            A.RandomBrightnessContrast(p=0.3),
            A.HueSaturationValue(p=0.2),
            A.GaussNoise(p=0.2),
            A.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
            ToTensorV2(),
        ])
    else:
        return A.Compose([
            A.Resize(img_size, img_size),
            A.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
            ToTensorV2(),
        ])


class ProductClassifier(nn.Module):
    """EfficientNet-B0 based product classifier."""
    
    def __init__(self, num_classes: int = NUM_CLASSES, pretrained: bool = True):
        super().__init__()
        self.backbone = timm.create_model("efficientnet_b0", pretrained=pretrained, num_classes=0)
        self.feature_dim = self.backbone.num_features
        self.classifier = nn.Sequential(
            nn.Dropout(0.3),
            nn.Linear(self.feature_dim, 512),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(512, num_classes)
        )
    
    def forward(self, x):
        features = self.backbone(x)
        return self.classifier(features)
    
    def get_features(self, x):
        return self.backbone(x)


def train_model(
    epochs: int = 20,
    batch_size: int = 16,
    lr: float = 1e-4,
    img_size: int = 224,
    device: str = "auto"
):
    """Train the product classifier."""
    if device == "auto":
        device = "cuda" if torch.cuda.is_available() else "cpu"
    
    logger.info(f"Training on {device}")
    
    # Data
    train_transform = get_transforms(train=True, img_size=img_size)
    val_transform = get_transforms(train=False, img_size=img_size)
    
    train_dataset = ProductDataset(TRAIN_DIR, transform=train_transform)
    val_dataset = ProductDataset(VAL_DIR, transform=val_transform)
    
    if len(train_dataset) == 0:
        raise ValueError(f"No training images found in {TRAIN_DIR}. Add images to class folders.")
    
    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True, num_workers=0)
    val_loader = DataLoader(val_dataset, batch_size=batch_size, shuffle=False, num_workers=0)
    
    # Model
    model = ProductClassifier(num_classes=NUM_CLASSES).to(device)
    criterion = nn.CrossEntropyLoss()
    optimizer = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=1e-4)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=epochs)
    
    best_val_acc = 0.0
    
    for epoch in range(epochs):
        # Train
        model.train()
        train_loss = 0.0
        train_correct = 0
        train_total = 0
        
        for images, labels in train_loader:
            images, labels = images.to(device), labels.to(device)
            
            optimizer.zero_grad()
            outputs = model(images)
            loss = criterion(outputs, labels)
            loss.backward()
            optimizer.step()
            
            train_loss += loss.item()
            _, predicted = outputs.max(1)
            train_total += labels.size(0)
            train_correct += predicted.eq(labels).sum().item()
        
        train_acc = 100. * train_correct / train_total
        
        # Validate
        model.eval()
        val_loss = 0.0
        val_correct = 0
        val_total = 0
        
        with torch.no_grad():
            for images, labels in val_loader:
                images, labels = images.to(device), labels.to(device)
                outputs = model(images)
                loss = criterion(outputs, labels)
                
                val_loss += loss.item()
                _, predicted = outputs.max(1)
                val_total += labels.size(0)
                val_correct += predicted.eq(labels).sum().item()
        
        val_acc = 100. * val_correct / val_total if val_total > 0 else 0
        
        logger.info(f"Epoch {epoch+1}/{epochs} | "
                    f"Train Loss: {train_loss/len(train_loader):.4f} Acc: {train_acc:.2f}% | "
                    f"Val Loss: {val_loss/len(val_loader) if len(val_loader) > 0 else 0:.4f} Acc: {val_acc:.2f}%")
        
        scheduler.step()
        
        # Save best model (use train_acc if no validation data)
        metric = val_acc if val_total > 0 else train_acc
        if metric > best_val_acc:
            best_val_acc = metric
            torch.save({
                "model_state_dict": model.state_dict(),
                "class_to_idx": train_dataset.class_to_idx,
                "epoch": epoch,
                "val_acc": val_acc,
                "train_acc": train_acc
            }, MODEL_PATH)
            logger.info(f"Saved best model (train_acc: {train_acc:.2f}%, val_acc: {val_acc:.2f}%)")
    
    # Also save final model
    torch.save({
        "model_state_dict": model.state_dict(),
        "class_to_idx": train_dataset.class_to_idx,
        "epoch": epoch,
        "val_acc": val_acc,
        "train_acc": train_acc
    }, MODEL_PATH.with_name("product_classifier_final.pth"))
    logger.info(f"Saved final model")
    with open(LABEL_MAP_PATH, "w") as f:
        json.dump(train_dataset.class_to_idx, f)
    
    logger.info(f"Training complete. Best val accuracy: {best_val_acc:.2f}%")
    return model


class ProductClassifierInference:
    """Inference wrapper for trained classifier."""
    
    def __init__(self, model_path: Path = MODEL_PATH, device: str = "auto"):
        if device == "auto":
            device = "cuda" if torch.cuda.is_available() else "cpu"
        self.device = device
        
        # Load label map
        if LABEL_MAP_PATH.exists():
            with open(LABEL_MAP_PATH) as f:
                self.class_to_idx = json.load(f)
        else:
            self.class_to_idx = {cls: i for i, cls in enumerate(CLASS_NAMES)}
        self.idx_to_class = {v: k for k, v in self.class_to_idx.items()}
        
        # Load model
        self.model = ProductClassifier(num_classes=NUM_CLASSES).to(device)
        if model_path.exists():
            checkpoint = torch.load(model_path, map_location=device)
            self.model.load_state_dict(checkpoint["model_state_dict"])
            logger.info(f"Loaded model from {model_path}")
        else:
            logger.warning(f"No model found at {model_path}, using random weights")
        self.model.eval()
        
        self.transform = get_transforms(train=False, img_size=224)
    
    @torch.no_grad()
    def predict(self, image_bytes: bytes, top_k: int = 3) -> List[Dict]:
        """Predict product class from image bytes."""
        try:
            image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
            image = np.array(image)
            augmented = self.transform(image=image)
            image_tensor = augmented["image"].unsqueeze(0).to(self.device)
            
            outputs = self.model(image_tensor)
            probs = torch.softmax(outputs, dim=1)[0]
            
            top_probs, top_indices = probs.topk(min(top_k, NUM_CLASSES))
            
            results = []
            for prob, idx in zip(top_probs.cpu().numpy(), top_indices.cpu().numpy()):
                class_name = self.idx_to_class.get(idx, "other")
                info = CLASS_TO_STANDARD[class_name]
                results.append({
                    "class": class_name,
                    "confidence": float(prob),
                    "standard": info["standard"],
                    "description": info["description"],
                    "scheme": info["scheme"],
                    "keywords": info["keywords"]
                })
            
            return results
        except Exception as e:
            logger.error(f"Prediction error: {e}")
            return [{
                "class": "other",
                "confidence": 0.0,
                "standard": "Unknown",
                "description": "Classification failed",
                "scheme": "Manual classification required",
                "keywords": []
            }]
    
    def predict_best(self, image_bytes: bytes) -> Dict:
        """Get single best prediction."""
        results = self.predict(image_bytes, top_k=1)
        return results[0] if results else {
            "class": "other", "confidence": 0.0, "standard": "Unknown",
            "description": "Classification failed", "scheme": "Manual", "keywords": []
        }


# Global inference instance (lazy loaded)
_inference_instance = None


def get_classifier() -> ProductClassifierInference:
    """Get or create global classifier instance."""
    global _inference_instance
    if _inference_instance is None:
        _inference_instance = ProductClassifierInference()
    return _inference_instance


def classify_product_image(image_bytes: bytes) -> Dict:
    """Main entry point for product classification."""
    classifier = get_classifier()
    return classifier.predict_best(image_bytes)


if __name__ == "__main__":
    # Quick test
    import io
    logging.basicConfig(level=logging.INFO)
    
    # Check if model exists
    if MODEL_PATH.exists():
        classifier = ProductClassifierInference()
        # Test with prestige cooker
        with open("backend/tests/fixtures/scan_images/prestige_cooker.jpg", "rb") as f:
            result = classifier.predict(f.read())
            print(json.dumps(result, indent=2))
    else:
        print("No trained model found. Run train_model() first.")
        print(f"Add training images to: {TRAIN_DIR}")
        print("Structure: data/train/<class>/*.jpg")
        print(f"Classes: {CLASS_NAMES}")