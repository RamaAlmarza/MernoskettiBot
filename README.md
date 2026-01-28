# Basic Discord Bot

This is a basic Discord bot template written in Python using `discord.py`.

## Setup

1.  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

2.  **Configuration:**
    *   Copy `.env.example` to `.env`.
    *   Replace `your_token_here` with your actual Discord bot token.
    *   Set the Role IDs for permissions (Low Staff, Jr Mod, Mod, Sr Mod, Admin, Sr Admin).
    *   Set `STAR_CHANNEL_ID` for the `/star` command and automatic Starboard.
    *   Set `STAR_THRESHOLD` (default 5) for the automatic Starboard.

    ```bash
    cp .env.example .env
    ```

3.  **Run the Bot:**
    ```bash
    python3 main.py
    ```

## Features

All commands can be used with the prefix `!` or as Slash Commands (e.g., `/ping`).

*   `/ping`: Responds with "Pong!".
*   `/echo <message>`: Repeats the provided message.
*   `/roll [sides]`: Rolls a dice with the specified number of sides (default is 6).
*   `/8ball <question>`: Provides a magic 8-ball response to your question.
*   `/setup_ticket`: Creates a panel with a dropdown menu to open support tickets (Roles, Report Staff, Report User, Questions, Others).
    *   **Ticket Controls:** Tickets include a "Close Ticket" button for all users and a "Claim Ticket" button for staff (requires `manage_messages` permission).

## Moderation

*   `/mute <member> <duration> [reason]`: Mutes a member. Requires **Low Staff** or higher.
*   `/unmute <member>`: Unmutes a member. Requires **Low Staff** or higher.
*   `/duration <member> <duration>`: Modifies the mute duration for a user. Requires **Low Staff** or higher.
*   `/warn <member> [reason]`: Warns a member. Requires **Jr Mod** or higher.
*   `/warn-remove <user_id> <warn_id>`: Removes a specific warning. Requires **Mod** or higher.
*   `/warnings <member>`: Lists warnings for a specific member. Requires **Jr Mod** or higher.
*   `/ban <member> [reason]`: Bans a member. Requires **Mod** or higher.
*   `/unban <user_id> [reason]`: Unbans a user. Requires **Mod** or higher.
*   `/kick <member> [reason]`: Kicks a member. Requires **Mod** or higher.
*   `/softban <member> [reason]`: Softbans a user. Requires **Sr Admin** or higher.
*   `/lock`: Locks the current channel. Requires **Admin** or higher.
*   `/unlock`: Unlocks the current channel. Requires **Admin** or higher.
*   `/temprole <member> <role> <duration>`: Gives a temporary role. Requires **Admin** or higher.
*   `/modlogs <user_id>`: Shows logs for a user. Requires **Sr Mod** or higher.
*   `/modstats <user_id>`: Shows stats of a moderator. Requires **Sr Admin** or higher.
*   `/moderations`: Shows recent moderation actions. Requires **Sr Admin** or higher.
*   `/case <case_id>`: Shows details of a specific moderation case. Requires **Admin** or higher.

## Notes

*   `/note <user_id> <text>`: Adds a note to a user. Requires **Low Staff** or higher.
*   `/delnote <user_id> <note_id>`: Deletes a specific note. Requires **Low Staff** or higher.
*   `/notes <user_id>`: Shows all notes for a user. Requires **Low Staff** or higher.
*   `/clearnotes <user_id>`: Clears all notes for a user. Requires **Sr Mod** or higher.
*   `/editnote <user_id> <note_id> <new_text>`: Edits a note. Requires **Sr Mod** or higher.

## Utilities

*   `/star <message_id>`: Sends a message to the starred channel. Requires **Low Staff** or higher.
*   `/av <user_id>`: Displays a user's avatar.

### Automatic Starboard

Messages that receive 5 (or configured `STAR_THRESHOLD`) ⭐ reactions are automatically posted to the configured `STAR_CHANNEL_ID` as an embed. If more stars are added, the count updates automatically.

## Utilities

*   `!sync`: Syncs the slash commands to the current guild immediately. Useful for testing. Requires Bot Owner permission.
