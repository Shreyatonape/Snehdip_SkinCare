from tensorflow.keras.preprocessing.image import ImageDataGenerator
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Conv2D, MaxPooling2D, Flatten, Dense, Dropout
from tensorflow.keras.optimizers import Adam
import json

# Image generators
train_datagen = ImageDataGenerator(
    rescale=1./255,
    rotation_range=20,
    horizontal_flip=True,
    zoom_range=0.15,
    shear_range=0.15,
    validation_split=0.2
)

# Data loading
train_data = train_datagen.flow_from_directory(
    'ml/dataset/train',
    target_size=(128,128),
    batch_size=32,
    class_mode='categorical',
    subset='training'
)

val_data = train_datagen.flow_from_directory(
    'ml/dataset/train',
    target_size=(128,128),
    batch_size=32,
    class_mode='categorical',
    subset='validation'
)

# ✅ FIX 1: Save labels correctly (index → class name)
labels = {v: k for k, v in train_data.class_indices.items()}
with open("ml/labels.json", "w") as f:
    json.dump(labels, f)

# Model
model = Sequential([
    Conv2D(32, (3,3), activation='relu', input_shape=(128,128,3)),
    MaxPooling2D(2,2),

    Conv2D(64, (3,3), activation='relu'),
    MaxPooling2D(2,2),

    Conv2D(128, (3,3), activation='relu'),
    MaxPooling2D(2,2),

    Flatten(),
    Dense(128, activation='relu'),
    Dropout(0.5),
    Dense(len(train_data.class_indices), activation='softmax')
])

model.compile(
    optimizer=Adam(learning_rate=0.001),
    loss='categorical_crossentropy',
    metrics=['accuracy']
)

# Train
model.fit(train_data, validation_data=val_data, epochs=15)

# ✅ FIX 2: Save model in NEW format (IMPORTANT)
model.save('ml/model.h5')

print("✅ Model trained and saved as ml/model.keras")
print("✅ Labels saved as ml/labels.json")