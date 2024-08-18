# Miner Fleet Management Application
This Python application is designed to manage the operation of a fleet of miners. It interacts with a mining control API to log in, configure profiles, adjust curtailment modes, and manage the state of miners based on a schedule. The application also includes a CLI interface for adding and removing miners.

## Features
- Automated Scheduling: Automatically configures miner profiles and curtails operation modes based on the time of day.
- CLI Management: Provides a command-line interface for adding, removing, and listing miners.
- Token Management: Handles authentication tokens for each miner, including automatic refresh when tokens expire.

## Installing Required Libraries
You can install the required Python libraries using pip:

'pip install requests schedule flask'

## How to Run the Application
1. Download or clone this repository to your local machine.

2. Navigate to the directory containing the script.
3. Run the API:
```bash
python app.py
```
4. Run the script:
```bash
python miner_management.py
```
The application will start by logging in all the miners in the list and initializing their states. It will then continuously run scheduled tasks and listen for CLI input.

5. Use the CLI to manage miners:

- Add a Miner: Enter add and provide the miner's IP address.
- Remove a Miner: Enter remove and provide the miner's IP address.
- List Miners: Enter list to view the current list of miners and their states.

## Scheduled Tasks
The application automatically schedules the following tasks:

- 00:00: Set all miners to overclock mode and active curtailment.
- 06:00: Set all miners to normal mode.
- 12:00: Set all miners to underclock mode.
- 18:00: Set all miners to sleep mode.

## Managing Miners
The CLI interface allows you to manage your miner fleet interactively:

- Adding a Miner: Enter the IP address of the new miner. The application will validate the IP, log in the miner, and initialize its state.
- Removing a Miner: Provide the IP address of the miner to remove. The application will log out the miner, remove it from the list, and clear its state.
- Listing Miners: Displays the current miners and their operating profiles.
