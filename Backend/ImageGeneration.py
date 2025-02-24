import asyncio
from random import randint
from PIL import Image
import requests
from dotenv import get_key
import os
from time import sleep


def open_images(prompt):
    folder_path = r"Data"  # Folder where the images are stored
    prompt = prompt.replace(" ", "_")
    # Generate the filenames for the images
    Files = [f"{prompt}{i}.jpg" for i in range(1, 5)]
    for jpg_file in Files:
        image_path = os.path.join(folder_path, jpg_file)
        try:
            img = Image.open(image_path)
            print(f"Opening image: {image_path}")
            img.show()
            sleep(1)  # Pause for 1 second before showing the next image
        except IOError:
            print(f"Unable to open {image_path}")

# API_URL = "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-xl-base-1.0"

API_URL = "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-2"
headers = {"Authorization": f"Bearer {get_key('.env', 'HuggingFaceAPIKey')}"}


# Async function to send a query to the Hugging Face API
async def query(payload):
    response = await asyncio.to_thread(requests.post, API_URL, headers=headers, json=payload)

    # Debugging: Print response status and content type
    print(f"API Response Code: {response.status_code}")
    print(f"API Response Content-Type: {response.headers.get('Content-Type')}")
    
    if response.status_code != 200:
        print(f"Error: API request failed with status code {response.status_code}")
        print(f"Response Text: {response.text}")  # Print error message
        return None

    # Ensure response is an image
    if "image" not in response.headers.get("Content-Type", ""):
        print("Error: API response is not an image")
        print(f"Response Content: {response.text}")  # Print response content
        return None

    return response.content  # Return valid image bytes



# Async function to generate images based on the given prompt


async def generate_images(prompt: str):
    folder_path = "Data"
    os.makedirs(folder_path, exist_ok=True)  # Ensure the folder exists

    tasks = []
    for _ in range(4):
        payload = {
            "inputs": f"{prompt}, quality=4K, sharpness=maximum, Ultra High details, high resolution, seed={randint(0, 1000000)}",
        }
        task = asyncio.create_task(query(payload))
        tasks.append(task)

    image_bytes_list = await asyncio.gather(*tasks)

    for i, image_bytes in enumerate(image_bytes_list):
        image_path = os.path.join(folder_path, f"{prompt.replace(' ', '_')}{i + 1}.jpg")
        
        # Ensure valid image response before saving
        if not image_bytes or len(image_bytes) < 1000:  # Check for valid image size
            print(f"Error: API did not return a valid image for {image_path}")
            continue

        with open(image_path, "wb") as f:
            f.write(image_bytes)

        print(f"Image saved: {image_path}")



def GenerateImages(prompt: str):
    asyncio.run(generate_images(prompt))  # Run the async image generation
    open_images(prompt)  # Open the generated images


# Main loop to monitor for image generation requests
while True:
    try:
        with open(r"Frontend\Files\ImageGeneration.data", "r") as f:
            lines = f.readlines()  # Read all lines
            
        if not lines:
            print("Error: File is empty. Waiting...")
            sleep(1)
            continue  # Wait until the file has content

        first_line = lines[0].strip()  # Take the first line and remove extra spaces/newlines
        print(f"Raw Data: '{first_line}'")  # Debugging: Shows exact content of the first line

        if "," not in first_line:
            print("Error: Data format is incorrect. Expected 'Prompt,Status'")
            sleep(1)
            continue  # Wait until the file has correct format

        Prompt, Status = first_line.split(",", 1)  # Only split on first comma

        # Debugging: Print the exact values and lengths to check hidden characters
        print(f"Prompt: '{Prompt.strip()}' (Length: {len(Prompt.strip())})")
        print(f"Status: '{Status.strip()}' (Length: {len(Status.strip())})")

        if Status.strip().casefold() == "true":  # More robust comparison
            print("Generating Images ... ")  # This should print now

            GenerateImages(Prompt.strip())

            # Reset status in file after generating images
            with open(r"Frontend\Files\ImageGeneration.data", "w") as f:
                f.write("False, False")
            break  # Exit loop after processing request

        else:
            print(f"Status '{Status.strip()}' is not 'True'. Waiting...")
            sleep(1)
            
    except:
        pass