import streamlit as st
import os
import numpy as np
from keras.models import load_model
from keras.layers import DepthwiseConv2D
from keras.preprocessing import image
from keras.applications.mobilenet_v2 import preprocess_input  # Adjust according to your model
import openai

# OpenAI API key (ensure this is loaded securely from your environment or .env file)
openai.api_key = os.getenv("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")

# Custom DepthwiseConv2D class to handle loading without 'groups' argument
class CustomDepthwiseConv2D(DepthwiseConv2D):
    def __init__(self, *args, **kwargs):
        # Remove unsupported 'groups' argument if present
        kwargs.pop('groups', None)
        super().__init__(*args, **kwargs)

# Function to load the model
def load_model_func():
    model_path = 'waste_classification.h5'  # or provide the absolute path
    if not os.path.isfile(model_path):
        raise FileNotFoundError(f"Model file not found: {model_path}")
    
    # Load the model with custom_objects
    model = load_model(model_path, custom_objects={'DepthwiseConv2D': CustomDepthwiseConv2D})
    return model

# Load the labels from the labels file
def load_labels():
    labels_path = 'labels.txt'  # or provide the absolute path
    if not os.path.isfile(labels_path):
        raise FileNotFoundError(f"Labels file not found: {labels_path}")

    with open(labels_path, 'r') as file:
        labels = file.read().splitlines()
    return labels

# Function to preprocess the uploaded image
def preprocess_image(uploaded_file):
    img = image.load_img(uploaded_file, target_size=(224, 224))  # Adjust according to your model's input size
    img_array = image.img_to_array(img)
    img_array = np.expand_dims(img_array, axis=0)  # Add batch dimension
    img_array = preprocess_input(img_array)  # Preprocess for your model (e.g., MobileNetV2)
    return img_array

# Function to classify an image
def classify_image(model, labels, image_data):
    predictions = model.predict(image_data)
    predicted_label = labels[np.argmax(predictions)]
    return predicted_label

# Function to get recycling suggestions using OpenAI
def get_openai_suggestions(predicted_label):
    try:
        # Customize the prompt based on the waste type
        prompt = f"Provide suggestions for handling {predicted_label} waste responsibly."

        # Call OpenAI API to generate suggestions
        response = openai.Completion.create(
            model="text-davinci-003",
            prompt=prompt,
            max_tokens=150,
            temperature=0.7
        )

        suggestions = response.choices[0].text.strip()
        return suggestions
    except Exception as e:
        return f"Error getting suggestions from OpenAI: {str(e)}"

# Show classification page
def show_classification_page():
    # Streamlit app layout
    st.markdown('<div class="header-title">EcoSort</div>', unsafe_allow_html=True)
    st.write("Select an option to classify waste:")

    # Add radio button for choosing the input method
    option = st.radio("Choose input method:", ("Upload Image", "Use Webcam"))

    # Load the model and labels when the app starts
    model, labels = None, None

    try:
        model = load_model_func()
    except Exception as e:
        st.error(f"Error loading model: {e}")

    try:
        labels = load_labels()
    except Exception as e:
        st.error(f"Error loading labels: {e}")

    # Handle image upload
    if option == "Upload Image":
        uploaded_file = st.file_uploader("Choose an image...", type=["jpg", "jpeg", "png"])

        if uploaded_file is not None:
            # Display uploaded image
            st.image(uploaded_file, caption='Uploaded Image', use_column_width=True)
            st.write("")

            # Preprocess the image and make predictions using the model
            image_data = preprocess_image(uploaded_file)
            if model and labels:
                predicted_label = classify_image(model, labels, image_data)
                st.write(f"Predicted label: **{predicted_label}**", unsafe_allow_html=True)

                # Get recycling suggestions from OpenAI
                suggestions = get_openai_suggestions(predicted_label)
                st.subheader("Recycling Suggestions:")
                st.markdown(f'<div class="suggestion">{suggestions}</div>', unsafe_allow_html=True)
            else:
                st.error("Model or labels not available. Please check if they were loaded correctly.")

    # Handle webcam capture
    if option == "Use Webcam":
        camera_input = st.camera_input("Take a picture")
        
        if camera_input is not None:
            # Display the captured image
            st.image(camera_input, caption='Captured Image', use_column_width=True)
            st.write("")

            # Preprocess the image and make predictions using the model
            image_data = preprocess_image(camera_input)
            if model and labels:
                predicted_label = classify_image(model, labels, image_data)
                st.write(f"Predicted label: **{predicted_label}**", unsafe_allow_html=True)

                # Get recycling suggestions from OpenAI
                suggestions = get_openai_suggestions(predicted_label)
                st.subheader("Recycling Suggestions:")
                st.markdown(f'<div class="suggestion">{suggestions}</div>', unsafe_allow_html=True)
            else:
                st.error("Model or labels not available. Please check if they were loaded correctly.")

# Main application
if __name__ == "__main__":
    show_classification_page()
