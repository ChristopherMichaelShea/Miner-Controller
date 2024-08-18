import requests
import schedule
import time
from datetime import datetime
import threading
import ipaddress

# Configuration for miners
miners = ['192.192.1.1', '192.192.1.2']  # Initial list of miner IPs
api_base_url = "http://localhost:5000/api"  # Base URL of the mining control API
miner_auth_tokens = {}  # Miner login auth tokens and their TTLs
miner_operation_states = {}  # Current state (profile, curtail) of each miner

def authenticate_and_login_miner(miner_ip):
    try:
        response = requests.post(f"{api_base_url}/login", json={'miner_ip': miner_ip})
        response.raise_for_status()
        data = response.json()
        
        token = data.get('token')
        token_expiry_time = data.get('ttl')
        
        if token and token_expiry_time:
            miner_auth_tokens[miner_ip] = {'token': token, 'ttl': token_expiry_time}
            print(f"Miner {miner_ip} logged in with token {token} and TTL {token_expiry_time}.")
        else:
            print(f"Invalid response data for miner {miner_ip}: {data}")
    except requests.RequestException as e:
        print(f"Failed to login miner {miner_ip}. Error: {e}")

def deauthenticate_and_logout_miner(miner_ip):
    try:
        response = requests.post(f"{api_base_url}/logout", json={'miner_ip': miner_ip})
        response.raise_for_status()
        if response.status_code == 200:
            miners.remove(miner_ip)
            miner_auth_tokens.pop(miner_ip, None)
            miner_operation_states.pop(miner_ip, None)
            print(f"Miner {miner_ip} successfully logged out.")
        else:
            print(f"Failed to log out miner {miner_ip}. Error: {response.json()}")
    except requests.RequestException as e:
        print(f"Failed to log out miner {miner_ip}. Error: {e}")

def configure_miner_profile(miner_ip, operating_profile):
    token_data = miner_auth_tokens.get(miner_ip)

    if token_data:
        refresh_miner_token_if_expired(miner_ip, token_data)

        token = token_data.get('token')

        try:
            response = requests.post(f"{api_base_url}/profileset", json={'token': token, 'profile': operating_profile})
            response.raise_for_status()
            if response.status_code == 200:
                miner_operation_states[miner_ip]['profile'] = operating_profile
                print(f"Miner {miner_ip}: {response.json().get('message')}")
            else:
                print(f"Failed to set profile for miner {miner_ip}. Error: {response.json()}")
        except requests.RequestException as e:
            print(f"Failed to set profile for miner {miner_ip}. Error: {e}")
    else:
        print(f"Miner {miner_ip} is not logged in.")

def adjust_miner_curtailment(miner_ip, curtailment_mode):
    token_data = miner_auth_tokens.get(miner_ip)

    if token_data:
        refresh_miner_token_if_expired(miner_ip, token_data)

        token = token_data.get('token')

        try:
            response = requests.post(f"{api_base_url}/curtail", json={'token': token, 'mode': curtailment_mode})
            response.raise_for_status()
            if response.status_code == 200:
                miner_operation_states[miner_ip]['curtail'] = curtailment_mode
                print(f"Miner {miner_ip}: {response.json().get('message')}")
            else:
                print(f"Failed to curtail miner {miner_ip}. Error: {response.json()}")
        except requests.RequestException as e:
            print(f"Failed to curtail miner {miner_ip}. Error: {e}")
    else:
        print(f"Miner {miner_ip} is not logged in.")

def refresh_miner_token_if_expired(miner_ip, token_data):
    if token_data:
        # Convert TTL string to a datetime object
        ttl_str = token_data.get('ttl')
        token_expiry_time = datetime.strptime(ttl_str, '%a, %d %b %Y %H:%M:%S %Z')

        # Check if the token has expired and refresh if necessary
        if token_expiry_time < datetime.utcnow():
            authenticate_and_login_miner(miner_ip)

def initialize_miner_operation_state(miner_ip):
    #Initializes the state of a miner based on the current time.

    current_time = datetime.now().time()

    if miner_ip not in miner_operation_states:
        miner_operation_states[miner_ip] = {'curtail': None, 'profile': None}

    if current_time >= datetime.strptime("18:00", "%H:%M").time():
        adjust_miner_curtailment(miner_ip, 'sleep')
    else:
        adjust_miner_curtailment(miner_ip, 'active')

    if current_time >= datetime.strptime("00:00", "%H:%M").time() and current_time < datetime.strptime("06:00", "%H:%M").time():
        configure_miner_profile(miner_ip, 'overclock')
    elif current_time >= datetime.strptime("06:00", "%H:%M").time() and current_time < datetime.strptime("12:00", "%H:%M").time():
        configure_miner_profile(miner_ip, 'normal')
    elif current_time >= datetime.strptime("12:00", "%H:%M").time() and current_time < datetime.strptime("18:00", "%H:%M").time():
        configure_miner_profile(miner_ip, 'underclock') 

def schedule_miner_tasks():
    # Overclock from 00:00 to 06:00
    # Normal from 06:00 to 12:00
    # Underclock from 12:00 to 18:00
    # Curtail (sleep) from 18:00 to 00:00

    schedule.every().day.at("00:00").do(lambda: [configure_miner_profile(ip, 'overclock') or adjust_miner_curtailment(ip, 'active') for ip in miners])
    schedule.every().day.at("06:00").do(lambda: [configure_miner_profile(ip, 'normal') for ip in miners])
    schedule.every().day.at("12:00").do(lambda: [configure_miner_profile(ip, 'underclock') for ip in miners])
    schedule.every().day.at("18:00").do(lambda: [adjust_miner_curtailment(ip, 'sleep') for ip in miners])

def display_current_miners_with_cli():
    print("Current Miners and their States:")
    for miner_ip in miners:
        profile = miner_operation_states.get(miner_ip, 'profile')
        print(f"Miner IP: {miner_ip} | Profile: {profile}")

def add_miner_with_cli():
    while True:
        new_miner_ip = input("Enter the IP address of the new miner. Enter 'back' to go back: ")
               
        if new_miner_ip.lower() == 'back':
            break

        try:
            # Validate IP address format
            ipaddress.ip_address(new_miner_ip)
            # If valid, add the miner
            if new_miner_ip not in miners:
                miners.append(new_miner_ip)
                authenticate_and_login_miner(new_miner_ip)
                initialize_miner_operation_state(new_miner_ip)
                print(f"Miner {new_miner_ip} added.")
            else:
                print("Miner IP already exists.")
        except ValueError:
            print("Invalid IP address. Please enter a valid IP.")

def remove_miner_with_cli():
    while True:
        remove_miner_ip = input("Enter the IP address of the miner to remove. Enter 'back' to go back: ")

        if remove_miner_ip.lower() == 'back':
            break

        if remove_miner_ip in miners:
            deauthenticate_and_logout_miner(remove_miner_ip)
            print(f"Miner {remove_miner_ip} removed.")
        else:
            print("Miner IP not found.")

def manage_miners_with_cli():
    while True:
        user_input = input("Enter 'add' to add a miner, 'remove' to remove a miner, 'list' to list miners: ").lower()

        if user_input == 'add':
            add_miner_with_cli()
        elif user_input == 'remove':
            remove_miner_with_cli()
        elif user_input == 'list':
            display_current_miners_with_cli()
        else:
            print("Invalid input. Please enter 'add', 'remove', or 'list'.")

def main():
    # Log in all miners and initialize their states
    for miner_ip in miners:
        authenticate_and_login_miner(miner_ip)
        initialize_miner_operation_state(miner_ip)
    
    schedule_miner_tasks()

    # Start a separate thread to handle CLI input for managing miners
    cli_thread = threading.Thread(target=manage_miners_with_cli, daemon=True)
    cli_thread.start()

    while True:
        schedule.run_pending()
        time.sleep(1)

if __name__ == "__main__":
    main()
