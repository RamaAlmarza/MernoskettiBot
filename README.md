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

*   `!ping`: Responds with "Pong!".
*   `!echo <message>`: Repeats the provided message.
*   `!roll [sides]`: Rolls a dice with the specified number of sides (default is 6).
*   `!8ball <question>`: Provides a magic 8-ball response to your question.
*   `!setup_ticket`: Creates a panel with a button to open support tickets.