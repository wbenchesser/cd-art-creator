import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
import numpy as np
import requests
from dotenv import load_dotenv
import os

# Load sensitive environment variables from .env file
load_dotenv()

# Spotify API credentials
client_id = os.getenv("SPOTIFY_CLIENT_ID")
client_secret = os.getenv("SPOTIFY_CLIENT_SECRET")

# Spotify Authentication
sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials(client_id=client_id, client_secret=client_secret))

def main():
    # get playlist and cover color input from user 
    playlist_link = input('Enter the spotify link to your playlist: ')

    print("Enter the following for the starting gradient color (as RGB): ")
    color1 = get_color_inputs() # (255, 0, 0) Example color red

    print("Enter the following for the starting gradient color (as RGB): ")
    color2 = get_color_inputs() # (0, 0, 255) Example color blue

    playlist_title = get_playlist_title(playlist_link)
    tracks = get_playlist_tracks(playlist_link)
    track_info = [(track['track']['name'], track['track']['artists'][0]['name'], track['track']['album']['images'][0]['url']) for track in tracks]

    width, height = 1000, 1000  

    # Create 5 x 5 pixelated gradient from input colors
    gradient_image = create_pixelated_gradient(color1, color2, width, height)
    gradient_image.save('gradient.png')

    # Overlay playlist title on gradient image
    image_with_text = overlay_text_on_image(gradient_image, playlist_title)
    image_with_text.save('gradient_with_text.png')

    # Create the formatted tracklist image
    text_image = create_tracklist(track_info, width, height)
     # Save it upside down so when printed and folded it will be right-side up
    text_image = text_image.rotate(180)
    text_image.save('tracklist.png')

    # Create the collage of all the album covers for the back cover
    collage_image = create_collage(track_info, width, height)
    collage_image.save('collage.png')

    # Compile all of the images into one printable master image
    cd_sleeve = create_cd_sleeve(gradient_image, text_image, collage_image)
    cd_sleeve.save('cd_sleeve_art.png')

def get_color_inputs():
    """Gathers three inputs from the user, corresponding to the three
    values of an RGB code and turns it into an RGB color object."""
    try:
        red = int(input("Enter the red component (0-255): "))
        green = int(input("Enter the green component (0-255): "))
        blue = int(input("Enter the blue component (0-255): "))
        
        if 0 <= red <= 255 and 0 <= green <= 255 and 0 <= blue <= 255:
            rgb_color = (red, green, blue)
            return rgb_color
        else:
            print("Error: RGB components must be in the range 0-255.")
            return get_color_inputs()
    except ValueError:
        print("Error: Please enter valid integer values for RGB components.")
        return get_color_inputs()

def get_playlist_title(playlist_link):
    """Returns the spotify playlist name given the link to the playlist"""
    playlist = sp.playlist(playlist_link)
    return playlist['name']

def get_playlist_tracks(playlist_link):
    """Returns a list of tracks containing dictionaries
      representing each track from the playlist"""
    results = sp.playlist_tracks(playlist_link)
    tracks = results['items']
    while results['next']:
        results = sp.next(results)
        tracks.extend(results['items'])
    return tracks

def create_pixelated_gradient(color1, color2, width, height):
    """Creates a minimilistic 5x5 pixel gradient moving from the first user entered
      color in the top left to the second user entered color in the bottom right"""
    grid_size = 5
    pixel_width = width // grid_size
    pixel_height = height // grid_size
    
    gradient = np.zeros((height, width, 3), dtype=np.uint8)
    
    for y in range(grid_size):
        for x in range(grid_size):
            ratio_x = x / (grid_size - 1)
            ratio_y = y / (grid_size - 1)
            ratio = (ratio_x + ratio_y) / 2  # average of x and y ratios

            r = int(color1[0] * (1 - ratio) + color2[0] * ratio)
            g = int(color1[1] * (1 - ratio) + color2[1] * ratio)
            b = int(color1[2] * (1 - ratio) + color2[2] * ratio)
            
            gradient[y*pixel_height:(y+1)*pixel_height, x*pixel_width:(x+1)*pixel_width] = [r, g, b]
    
    return Image.fromarray(gradient)

def overlay_text_on_image(image, text):
    """Overlays the gradient with the title of the Spotify playlist"""

    # Add text overlay for playlist title
    draw = ImageDraw.Draw(image)
    font = ImageFont.truetype('fonts/moonkids-ext-bd-font/MoonkidsPersonalUseExtbd-gxPZ3.ttf', 36)

    text_width = draw.textlength(text, font=font)
    text_height = font.size
    text_x = (image.width - text_width) // 2  # Centering text horizontally
    text_y = image.height - text_height - 20  # Positioning text near the bottom

    # Create black border around the text
    border_width = 2
    for dx in range(-border_width, border_width + 1):
        for dy in range(-border_width, border_width + 1):
            draw.text((text_x + dx, text_y + dy), text, font=font, fill='black')

    draw.text((text_x, text_y), text, fill='white', font=font)

    return image

def create_tracklist(tracks, width, height):
    """Creates a two-columned list of all tracks from the playlist
      with artists listed below each song"""
    image = Image.new('RGB', (width, height), color=(255, 255, 255))
    draw = ImageDraw.Draw(image)
    font = ImageFont.truetype('fonts/Meditative.ttf', 20)
    
    # Calculate column widths
    column_width = width // 2
    
    y_text = 10
    for i, track in enumerate(tracks):
        if i % 2 == 0:
            x_text = 10
        else:
            x_text = column_width
        
        line = f"{track[0]}"
        draw.text((x_text, y_text), line, font=font, fill=(0, 0, 0))

        line = f"   - {track[1]}"
        draw.text((x_text, (y_text + font.size)), line, font=font, fill=(0, 0, 0), italic=True)

        if i % 2 == 1:
            y_text += font.size * 3  # Additional space between pairs of tracks
    
    return image

def download_image(url):
    """Returns an ImageFile from a URL"""
    response = requests.get(url)
    img = Image.open(BytesIO(response.content))
    return img

def create_collage(tracks, width, height):
    """Needs rewrite to work for different numbers of images"""
    collage = Image.new('RGB', (width, height))
    img_size = width // 5  # Assuming 5 columns
    x_offset, y_offset = 0, 0

    for track in tracks:
        img = download_image(track[2])
        img = img.resize((img_size, img_size))
        collage.paste(img, (x_offset, y_offset))
        x_offset += img_size
        if x_offset >= width:
            x_offset = 0
            y_offset += img_size

    return collage

def create_cd_sleeve(gradient_image, text_image, collage_image):
    """Compiles all images into one printable master image"""
    sleeve_width = max(gradient_image.width, text_image.width, collage_image.width)
    sleeve_height = gradient_image.height + text_image.height + collage_image.height

    cd_sleeve = Image.new('RGB', (sleeve_width, sleeve_height))
    y_offset = 0

    cd_sleeve.paste(gradient_image, (0, y_offset))
    y_offset += gradient_image.height

    cd_sleeve.paste(text_image, (0, y_offset))
    y_offset += text_image.height

    cd_sleeve.paste(collage_image, (0, y_offset))

    return cd_sleeve

if __name__ == "__main__":
    main()