# Discord Moderation & Automation Bot

A Python-based Discord moderation and server management bot with MongoDB-backed persistence.

## Features

- Automated moderation actions
- Configurable punishment system
- Persistent server settings
- Event-driven command handling
- MongoDB integration
- Administrative tooling

## Technologies

- Python
- Discord.py
- MongoDB
- Discord APIs
- Async Programming

## Example Commands

!warn
!mute
!ban
Documentation will be posted upon completion

## Installation

1. Create a Discord Bot, by logging into the [Discord developer portal](https://discord.com/developers/home)
2. Copy the Discord bot token and put into a .env file named "variables.env" with variable named DISCORD_TOKEN="<insert token here>"
4. Create a MongoDB account and create a free database: https://www.mongodb.com/
5. Create a password for the database, and then copy the URL and put into the .env file named MONGODB_URL="<insert MongoDB link here>" (MAKE SURE YOUR ENV FILE IS IN YOUR GIT IGNORE AND IS NOT PUBLIC!)
6. Download all files.
7. Run "start.py"
