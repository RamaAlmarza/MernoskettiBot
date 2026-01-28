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
    *   Set `STAR_CHANNEL_ID` for the `/star` command.

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

*   `/mute <member> <duration> [reason]`: Mutes a member for the specified duration (e.g., 10m, 1h). Requires `moderate_members` permission.
*   `/duration <member> <duration>`: Modifies the mute duration for a user.
*   `/warn <member> [reason]`: Warns a member and logs it to the database. Requires `manage_messages` permission.
*   `/warn-remove <user_id> <warn_id>`: Removes a specific warning.
*   `/warnings <member>`: Lists warnings for a specific member. Requires `manage_messages` permission.
*   `/ban <member> [reason]`: Bans a member from the server. Requires `ban_members` permission.
*   `/unban <user_id> [reason]`: Unbans a user from the server using their ID. Requires `ban_members` permission.
*   `/kick <member> [reason]`: Kicks a member from the server.
*   `/softban <member> [reason]`: Bans and instantly unbans a user to delete their messages.
*   `/lock`: Locks the current channel (denies send messages).
*   `/unlock`: Unlocks the current channel.
*   `/temprole <member> <role> <duration>`: Gives a temporary role to a user.
*   `/modlogs <user_id>`: Shows all interactions (warns, mutes) with a user.
*   `/modstats <user_id>`: Shows statistics of a moderator's actions.
*   `/moderations`: Shows the last 50 moderation actions.

## Notes

*   `/note <user_id> <text>`: Adds a note to a user.
*   `/delnote <user_id> <note_id>`: Deletes a specific note.
*   `/notes <user_id>`: Shows all notes for a user.
*   `/clearnotes <user_id>`: Clears all notes for a user.
*   `/editnote <user_id> <note_id> <new_text>`: Edits a note.

## Utilities

*   `/star <message_id>`: Sends a message to the starred channel.
*   `/av <user_id>`: Displays a user's avatar.

## Utilities

*   `!sync`: Syncs the slash commands to the current guild immediately. Useful for testing. Requires Bot Owner permission.
