# ml/split_dataset.py

import os
import shutil
import pandas as pd
from sklearn.model_selection import train_test_split

# ---------------- Paths ----------------
raw_folder1 = "ml/dataset/raw/HAM10000_images_part_1"
raw_folder2 = "ml/dataset/raw/HAM10000_images_part_2"
metadata_path = "ml/dataset/raw/HAM10000_metadata.csv"

train_folder = "ml/dataset/train"
test_folder = "ml/dataset/test"

# ---------------- Disease classes ----------------
classes = ["akiec","bcc","bkl","df","mel","nv","vasc"]

# ---------------- Create train/test folders ----------------
for folder in [train_folder, test_folder]:
    for cls in classes:
        os.makedirs(os.path.join(folder, cls), exist_ok=True)

# ---------------- Load metadata ----------------
try:
    df = pd.read_csv(metadata_path)
except FileNotFoundError:
    print(f"❌ Metadata CSV not found at {metadata_path}")
    exit(1)

# ---------------- Split dataset ----------------
for cls in classes:
    images = df[df['dx'] == cls]['image_id'].tolist()
    
    if len(images) == 0:
        print(f"⚠️ No images found for class {cls}")
        continue

    # 80% train, 20% test
    train_imgs, test_imgs = train_test_split(images, test_size=0.2, random_state=42)

    for img_id in train_imgs:
        img_file = None
        for folder in [raw_folder1, raw_folder2]:
            path = os.path.join(folder, img_id + ".jpg")
            if os.path.exists(path):
                img_file = path
                break
        if img_file:
            shutil.copy(img_file, os.path.join(train_folder, cls, img_id + ".jpg"))
        else:
            print(f"⚠️ Train image not found: {img_id}.jpg")

    for img_id in test_imgs:
        img_file = None
        for folder in [raw_folder1, raw_folder2]:
            path = os.path.join(folder, img_id + ".jpg")
            if os.path.exists(path):
                img_file = path
                break
        if img_file:
            shutil.copy(img_file, os.path.join(test_folder, cls, img_id + ".jpg"))
        else:
            print(f"⚠️ Test image not found: {img_id}.jpg")

print("✅ Dataset successfully split into train and test!")