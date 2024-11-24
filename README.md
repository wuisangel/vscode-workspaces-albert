# Visual Studio Code Workspaces Albert Plugin

This is a plugin for the **[Albert Launcher](https://albertlauncher.github.io/)** which list and open VS Code workspaces and recently opened directories.
This plugin is inspired by the similar functionality available in PowerToys Run for Windows.

## Prerequisites

To use this plugin, you need to have the following installed on your system:

- Visual Studio Code
- sqlite3

## Installation

Follow these steps to install the plugin:

1. Open Albert and enable **Python plugin** in Albert settings
2. Open a terminal and navigate to `~/.local/share/albert/python/plugins` then clone this repository:
    ```sh
    git clone https://github.com/wuisangel/vscode-workspaces-albert.git
    ```
    or
    ```sh
    git clone https://github.com/wuisangel/vscode-workspaces-albert.git $HOME/.local/share/albert/python/plugins/vscode-workspaces-albert
    ```
4. Open Albert and enable the **VS Code Workspaces** plugin in Albert settings
5. Restart Albert

## Usage
Once the plugin is enabled, type `"{ "` in the Albert prompt to trigger the plugin. It will display your recent workspaces.

## Credits
This project is based on https://github.com/hankhjliao/albert-vscode-projects and has been updated to work with recent versions of Albert Launcher and its plugin system.

## License
MIT