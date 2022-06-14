# Beginner.Codes Discord Bot
This is the official Discord bot for the Beginner.Codes Discord server. A bit of a hodge podge of coding style and experience levels as it is a collaboration between various people, all of whom had no experience with Discord.py before this.

## Wanna Join Us?
If you'd like to join us, we're a welcoming community with over 1,000 members. [We will happily have you!!!](https://discord.gg/RGPs5TmqD5)

## Requirements
The bot uses [Poetry](https://python-poetry.org/) for packaging and dependency management. You will need to follow the [installation instructions](https://python-poetry.org/docs/#installation) before you can get started with the bot.

Additionally you will need a bot token from Discord. You can read about how to get yours [here](https://realpython.com/how-to-make-a-discord-bot-python/#creating-an-application).

## Configuration & Setup
First things first, we need to install the dependencies. To do that run:
```sh
poetry install
```

## Running
To run the bot you’ll need to be in the directory which you cloned the repo, and run the following command:
```sh
poetry run python -u -m dippy -c bot.yaml -t YOUR_DISCORD_TOKEN
```
This will create a virtual environment with all the required dependencies and run the Beginner.Codes bot using the experimental Dippy bot framework.
