# WorkInk Key Bot

## Overview
A Discord bot for managing Work Ink Key System. Users can request keys, validate them, and admins can manage user data.

## Project Structure
- `index.js` - Main bot entry point with all command handlers
- `package.json` - Node.js dependencies
- `database.json` - Local JSON file for storing user data and keys (auto-created)

## Commands

### User Commands
- `/ping` - Check if bot is online (shows latency)
- `/getkey <hwid>` - Get a key link for the specified HWID
  - **Admin Bypass:** Admins get key directly without clicking link
  - **Normal Users:** Get a link with checkpoint to complete
- `/checkkey <key> <hwid>` - Validate a key
- `/mykey` - View your stored key info
- `/keyinfo` - Information about the key system

### Admin Commands (requires admin role)
- `/stats` - View bot statistics
- `/resetuser <user>` - Reset a user's data
- `/broadcast <message>` - Send announcement

## Environment Variables (Required)
- `DISCORD_BOT_TOKEN` - Your Discord bot token
- `DISCORD_CLIENT_ID` - Your Discord application client ID
- `DISCORD_GUILD_ID` - The Discord server/guild ID
- `DISCORD_ADMIN_ROLE_ID` - Admin role ID for permissions
- `WORKINK_API_KEY` - Work Ink API key

## Running
The bot runs with `npm start` which executes `node index.js`.
