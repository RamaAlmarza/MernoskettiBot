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

## Moderation

*   `/mute <member> <duration> [reason]`: Mutes a member for the specified duration (e.g., 10m, 1h). Requires `moderate_members` permission.
*   `/warn <member> [reason]`: Warns a member and logs it to the database. Requires `manage_messages` permission.
*   `/warnings <member>`: Lists warnings for a specific member. Requires `manage_messages` permission.
*   `/ban <member> [reason]`: Bans a member from the server. Requires `ban_members` permission.
*   `/unban <user_id> [reason]`: Unbans a user from the server using their ID. Requires `ban_members` permission.

## Utilities

*   `!sync`: Syncs the slash commands to the current guild immediately. Useful for testing. Requires Bot Owner permission.
