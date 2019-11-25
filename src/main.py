import cv2
import re
import os
import argparse
import numpy as np
import pytesseract
import requests
import getpass
from glob import glob
from datetime import datetime
from .emis import authenticate, submit_expenses

# todo params:
# --no-image-process
# --dry-run
# --after-process move/delete/nothing
# --move-path

class colors:
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    END = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

parser = argparse.ArgumentParser(description='EMIS Lunch Expenses Scanner')
parser.add_argument('-u', '--username',
                    default='',
                    help='your EMIS username')
parser.add_argument('-p', '--password',
                    default='',
                    help='your EMIS password, not adviced to use due bad opsec')
parser.add_argument('path',
                    metavar='PATH',
                    type=str,
                    default='~/',
                    help='file or directory path, default: "~/"')
parser.add_argument('-r', '--recursive',
                    default=False,
                    action='store_true',
                    help='recursive folder searching, default: "False"')
parser.add_argument('-s', '--skip',
                    default=False,
                    action='store_true',
                    help='auto submit and skip if any either date or price are missing, default: "False"')
parser.add_argument('-i', '--show-image',
                    default=False,
                    action='store_true',
                    help='show the processed result image, default: "False"')
parser.add_argument('-t', '--show-text',
                    default=False,
                    action='store_true',
                    help='show the processed text from the image, default: "False"')
parser.add_argument('-l', '--lang',
                    default='nld',
                    help='the Tesseract language to use, default: "nld"')

ACTION_CHOICES = ['submit', 'skip', 'set price', 'set date', 'show image', 'exit']

# TODO  `clear` on linux, `cls` on win, dunno on mac
clear = lambda: os.system('clear')

def get_images(path, recursive=False):
    images = []

    if os.path.isfile(path):
        images = [path]
    elif os.path.isdir(path):
        result = [glob(f'{path.rstrip("/")}/{ext}', recursive=recursive) for ext in ['*.png', '*.jpg']]
        # flatting list of lists
        images = [item for sublist in result for item in sublist]

    return images

def clean_date_string(date_str):
    replace = [' ', '—', '/']

    for x in replace:
        date_str = date_str.replace(x, '-')

    return date_str

def get_api_key():
    api_key = None
    try:
        with open('emis.key', 'r') as file:
            api_key = file.read()
    except IOError:
        pass

    if not api_key:
        print(f'{colors.RED}EMIS API key not found!{colors.END}')
        with open('emis.key', 'w') as file:
            api_key = input('API key: ').rstrip('\n')
            file.write(api_key)

    return api_key

def main():
    clear()

    api_key = get_api_key()

    args = parser.parse_args()

    if not args.username:
        args.username = input('Username: ')

    if not args.password:
        args.password = getpass.getpass('Password: ')

    images = get_images(args.path, recursive=args.recursive)

    if not images:
        print(f'No images found at "{args.path}"')
        return

    for image in images:
        clear()
        print(f'Processing "{image}"...')

        original_image = cv2.imread(image, cv2.IMREAD_COLOR)
        grayscale_image = cv2.cvtColor(original_image, cv2.COLOR_BGR2GRAY)
        gaussian_image = cv2.adaptiveThreshold(grayscale_image, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)
        threshold, threshold_image = cv2.threshold(gaussian_image, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        result_image = cv2.medianBlur(threshold_image, 5)

        text = pytesseract.image_to_string(result_image, config=(f'--tessdata-dir ./data -l {args.lang} --oem 1 --psm 3'))

        prices_matches = re.findall(r'^.*(\d+ *[,\.]{1} *\d{2}).*$', text, re.MULTILINE)
        if prices_matches:
            prices_matches = list(map(lambda x: float(x.replace(',', '.').replace(' ', '')), prices_matches))
            prices_matches = list(set(prices_matches))
            prices_matches.sort(reverse=True)

        date_match = re.search(r'^.*(\d{2}[ \-—\/]+\d{2}[ \-—\/]+\d{4}).*$', text, re.MULTILINE)
        if date_match:
            try:
                date = datetime.strptime(clean_date_string(date_match.group(1)), '%d-%m-%Y').strftime('%Y-%m-%d')
            except ValueError:
                date = None

        properties = {
            'args': args,
            'image': image,
            'result_image': result_image,
            'price': prices_matches[0] if prices_matches else 0,
            'over_limit': False,
            'date': date if date_match else None,
            'text': text,
            'api_key': api_key,
        }

        if properties['price'] and properties['price'] > 7.0:
            properties['price_original'] = properties['price']
            properties['price'] = 7.0
            properties['over_limit'] = True

        if args.show_image:
            named_window = cv2.namedWindow('Preview', cv2.WINDOW_NORMAL)
            cv2.resizeWindow('Preview', 1000, 1000)
            cv2.imshow('Preview', result_image)
            cv2.waitKey(0)
            cv2.destroyAllWindows()

        if args.skip:
            if not properties['date'] or properties['price'] <= 0:
                continue

            submit(properties)

        print_results(properties)
        do_input_action(properties)

def print_results(properties):
    clear()

    print(f'Results for "{colors.BOLD}{properties["image"]}{colors.END}"\n')

    if properties['args'].show_text:
        print(f'\n{colors.BOLD}Found text:{colors.END}\n{properties["text"]}\n')

    price_color = colors.GREEN
    price_message = ''

    if not properties['price']:
        price_color = colors.RED
        price_message = 'No price found, please set or skip'
    elif properties['over_limit']:
        price_color = colors.YELLOW
        price_message = f'Over the limit, adjusted to 7.00 EUR (was {properties["price_original"]} EUR)'

    print(f'Price: {price_color}{colors.BOLD}{properties["price"]} EUR{colors.END} {price_message}')

    if not properties['date']:
        print(f'Date: {colors.RED}{colors.BOLD}?{colors.END} No date found, please set or skip')
    else:
        print(f'Date: {colors.GREEN}{colors.BOLD}{properties["date"]}{colors.END}')

def do_input_action(properties):
    input_str = ' | '.join([f'{colors.BOLD}{colors.YELLOW}{key}. {value.capitalize()}{colors.END}' for key, value in enumerate(ACTION_CHOICES, start=1)])

    try:
        response = int(input(f'\n{input_str}\nMake your choice: '))
    except ValueError:
        print(f'{colors.RED}Invalid choice [1-{len(ACTION_CHOICES)}]{colors.END}')
        do_input_action(properties)
    except KeyboardInterrupt:
        exit()

    # Not between the valid number range
    if 0 < response > len(ACTION_CHOICES):
        print(f'{colors.RED}Invalid choice [1-{len(ACTION_CHOICES)}]{colors.END}')
        do_input_action(properties)

    # Choice not found
    if not ACTION_CHOICES[response - 1]:
        print(f'{colors.RED}Invalid choice [1-{len(ACTION_CHOICES)}]{colors.END}')
        do_input_action(properties)

    action = ACTION_CHOICES[response - 1].replace(' ', '_')

    if action in globals():
        globals()[action](properties)
    else:
        print(f'{colors.RED}Action not defined ({action}){colors.END}')
        do_input_action(properties)

def submit(properties):
    token = authenticate(properties['api_key'],
        properties['args'].username, properties['args'].password)
    response = submit_expenses(properties['api_key'], token, properties)

    if response.status_code is not 201:
        print_results(properties)
        print(f'{colors.RED}Submiting expenses failed ({response.status_code} {response.json().get("message")}){colors.END}')
        do_input_action(properties)

def skip(properties):
    pass

def set_price(properties):
    try:
        properties['price'] = float(input('Set price: '))
    except ValueError:
        pass

    print_results(properties)
    do_input_action(properties)

def set_date(properties):
    properties['date'] = input('Set date (YYYY-MM-DD): ')

    print_results(properties)
    do_input_action(properties)

def show_image(properties):
    named_window = cv2.namedWindow('Preview', cv2.WINDOW_NORMAL)
    cv2.resizeWindow('Preview', 1000, 1000)
    cv2.imshow('Preview', properties['result_image'])
    cv2.waitKey(0)
    cv2.destroyAllWindows()

    do_input_action(properties)

def exit(properties=None):
    cv2.destroyAllWindows()

    clear()
    print('Bye!')

    quit()

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        exit()
