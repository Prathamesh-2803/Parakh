#!/usr/bin/env python
"""Train the product classifier model."""

import sys
import os
import argparse

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from backend.app.tools.product_classifier import train_model
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")

def parse_args():
    parser = argparse.ArgumentParser(description="Train Parakh Product Classifier")
    parser.add_argument("--epochs", type=int, default=20, help="Number of epochs")
    parser.add_argument("--batch-size", type=int, default=16, help="Batch size")
    parser.add_argument("--lr", type=float, default=1e-4, help="Learning rate")
    parser.add_argument("--auto", action="store_true", help="Auto-continue without prompt")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    
    print("=" * 60)
    print("Parakh Product Classifier Training")
    print("=" * 60)
    print()
    print("Required folder structure:")
    print("  data/train/bottle/*.jpg")
    print("  data/train/bulb/*.jpg")
    print("  data/train/helmet/*.jpg")
    print("  data/train/gold_jewelry/*.jpg")
    print("  data/train/pressure_cooker/*.jpg")
    print("  data/train/other/*.jpg")
    print("  data/val/<same classes>/*.jpg")
    print()
    print("Add 20-50 images per class for decent accuracy.")
    print("Current images: 1 per class (from test fixtures)")
    print()
    
    # Check data
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    train_dir = os.path.join(project_root, "data", "train")
    total = 0
    for cls in os.listdir(train_dir):
        cls_path = os.path.join(train_dir, cls)
        if os.path.isdir(cls_path):
            count = len([f for f in os.listdir(cls_path) if f.lower().endswith(('.jpg', '.jpeg', '.png'))])
            print(f"  {cls}: {count} images")
            total += count
    
    print(f"\nTotal training images: {total}")
    
    if total < 6 and not args.auto:
        print("\nWARNING: Very few images! Add more images to each class folder.")
        print("   You can download from Google Images or take photos.")
        response = input("\nContinue training anyway? (y/N): ")
        if response.lower() != 'y':
            sys.exit(0)
    elif total < 6:
        print("\nWARNING: Very few images! Continuing with --auto flag...")
    
    print("\nStarting training...")
    try:
        train_model(epochs=args.epochs, batch_size=args.batch_size, lr=args.lr)
        print("\nTraining complete!")
        print(f"Model saved to: data/models/product_classifier.pth")
    except Exception as e:
        print(f"\nTraining failed: {e}")
        sys.exit(1)