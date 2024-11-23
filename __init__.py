# -- coding: utf-8 --

import os
import json
import unicodedata
import sqlite3
from pathlib import Path
from albert import *

md_iid = "2.3"
md_version = "1.0"
md_name = "VS Code Workspaces"
md_description = "List and open VS Code Workspaces and recently opened directories."
md_license = "MIT"
md_url = "https://github.com/wuisangel/vscode-workspaces-albert"
md_authors = "@wuisangel"
md_maintainers = "@wuisangel"
md_bin_dependencies = ["sqlite3"]

# Paths
HOME_DIR = os.environ["HOME"]
EXEC = "/usr/bin/code"
VARIANT = "Code"

# Storage paths for recent projects
STORAGE_DB_PATH = os.path.join(HOME_DIR, ".config", VARIANT, "User/globalStorage/state.vscdb")
STORAGE_JSON_PATHS = [
    os.path.join(HOME_DIR, ".config", VARIANT, "storage.json"),
    os.path.join(HOME_DIR, ".config", VARIANT, "User/globalStorage/storage.json"),
]

# Project Manager plugin configuration path
PROJECT_MANAGER_JSON_PATH = os.path.join(
    HOME_DIR, ".config", VARIANT, "User/globalStorage/alefragnani.project-manager/projects.json"
)

def normalize_string(input: str) -> str:
    """Normalize string for case and accent-insensitive comparison."""
    return ''.join(c for c in unicodedata.normalize("NFD", input) if unicodedata.category(c) != "Mn").lower()

class Plugin(PluginInstance, TriggerQueryHandler):
    def _init_(self):
        PluginInstance._init_(self)
        TriggerQueryHandler._init_(
            self,
            id=md_iid,
            name=md_name,
            description=md_description,
            defaultTrigger= '{ ',
            synopsis="<search term>",
        )

    def handleTriggerQuery(self, query):
        if not query.isValid:
            return

        query_str = normalize_string(query.string)
        projects = []

        # Fetch recent projects from state.vscdb
        if os.path.exists(STORAGE_DB_PATH):
            try:
                con = sqlite3.connect(STORAGE_DB_PATH)
                cur = con.cursor()
                cur.execute('SELECT value FROM ItemTable WHERE key = "history.recentlyOpenedPathsList"')
                result = cur.fetchone()
                if result:
                    paths = json.loads(result[0]).get("entries", [])
                    for entry in paths:
                        uri = entry.get("folderUri", "")
                        if uri.startswith("file://"):
                            path = uri.replace("file://", "")
                            if query_str in normalize_string(path):
                                projects.append({
                                    "name": os.path.basename(path),
                                    "path": path,
                                })
            except Exception as e:
                warning(f"Error reading state.vscdb: {e}")

        # Fetch recent projects from legacy JSON files
        for json_path in STORAGE_JSON_PATHS:
            if os.path.exists(json_path):
                try:
                    with open(json_path, "r") as f:
                        config = json.load(f)
                        recent_paths = config.get("lastKnownMenubarData", {}).get("menus", {}).get("File", {}).get("items", [])
                        for item in recent_paths:
                            if "Open &&Recent" in item.get("label", ""):
                                for sub_item in item.get("submenu", {}).get("items", []):
                                    uri = sub_item.get("uri", {}).get("external", "")
                                    if query_str in normalize_string(uri):
                                        projects.append({
                                            "name": os.path.basename(uri),
                                            "path": uri,
                                        })
                except Exception as e:
                    warning(f"Error reading {json_path}: {e}")

        # Fetch projects from Project Manager plugin
        if os.path.exists(PROJECT_MANAGER_JSON_PATH):
            try:
                with open(PROJECT_MANAGER_JSON_PATH, "r") as f:
                    project_manager_projects = json.load(f)
                    for project in project_manager_projects:
                        if query_str in normalize_string(project.get("rootPath", "")):
                            projects.append({
                                "name": project.get("name", "Unnamed"),
                                "path": project.get("rootPath"),
                            })
            except Exception as e:
                warning(f"Error reading Project Manager JSON: {e}")

        # Add projects to query results
        for project in projects:
            query.add(StandardItem(
                id=project["path"],
                text=project["name"],
                subtext=project["path"],
                iconUrls=[f"file:{Path(_file_).parent}/vscode.svg"],
                actions=[Action(
                    id="open",
                    text="Open in VS Code",
                    callable=lambda p=project["path"]: runDetachedProcess([EXEC, p]),
                )],
            ))