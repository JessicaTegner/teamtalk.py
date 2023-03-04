# Teamtalk.py

[![Documentation](https://img.shields.io/readthedocs/teamtalkpy?style=flat-square)](http://teamtalkpy.readthedocs.io/en/latest)
[![Build Status](https://github.com/JessicaTegner/teamtalk.py/actions/workflows/ci.yaml/badge.svg)](https://github.com/JessicaTegner/teamtalk.py/actions/workflows/ci.yaml)
[![GitHub Releases](https://img.shields.io/github/tag/JessicaTegner/teamtalk.py.svg?style=flat-square)](https://github.com/JessicaTegner/teamtalk.py/releases)
[![PyPI Version](https://img.shields.io/pypi/v/teamtalk.py?style=flat-square)](https://pypi.org/project/teamtalk.py/)
[![Python versions](https://img.shields.io/pypi/pyversions/teamtalk.py.svg?style=flat-square)](https://pypi.python.org/pypi/teamtalk.py/)
![License](https://img.shields.io/pypi/l/pypandoc.svg?style=flat-square)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg?style=flat-square)](http://makeapullrequest.com)

teamtalk.py is a simple but powerful pythonic library for making bots for the [TeamTalk5 Conferencing System](https://bearware.dk/)


### Installing

Python 3.8 or higher is required

#### From PyPI

```bash
pip install teamtalk.py
```

#### From source

```bash
git clone https://github.com/JessicaTegner/teamtalk.py
cd teamtalk.py
poetry install
```


### Usage

```python
import teamtalk

bot = teamtalk.TeamTalkBot()

@bot.event
async def on_ready():
    test_server = teamtalk.TeamTalkServerInfo("localhost", 10335, 10335, "user", "pass")
    await bot.add_server(test_server)

@bot.event
async def on_message(message):
    if message.content.lower() == "ping":
        message.reply("pong")

bot.run()
```


## Documentation

You can find the full documentation [here](http://teamtalkpy.readthedocs.io/en/latest)


## License

So you want to contribute to teamtalk.py? Great! There are many ways to contribute to this project, and all contributions are welcome.

If you have found a bug, have a feature request or want to help improve documentation please [open an issue](https://https://github.com/jessicaTegner/issues/new)_

You can also donate to the projects maintainer (JessicaTegner) to help support the development of teamtalk.py:


## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details
