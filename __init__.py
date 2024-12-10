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
md_description = "List and open VS Code Workspaces and recently opened directories and files."
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
    def __init__(self):
        PluginInstance.__init__(self)
        TriggerQueryHandler.__init__(
            self,
            id=md_iid,
            name=md_name,
            description=md_description,
            defaultTrigger= '{ ',
            synopsis="Project/Folder or File",
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
                        # Check if the File or Project/Folder exists in the operative system
                        if entry.get("folderUri", ""):
                            uri = entry.get("folderUri", "")
                        elif entry.get("fileUri", ""):
                            uri = entry.get("fileUri", "")
                        else:
                            continue
                        if uri.startswith("file://"):
                            path = uri.replace("file://", "")
                            if entry.get("folderUri", ""):
                                exists_in_os = True if os.path.isdir(path) else False
                            elif entry.get("fileUri", ""):
                                exists_in_os = True if os.path.isfile(path) else False
                            else:
                                exists_in_os = False
                            if not exists_in_os:
                                continue
                            # Check if project already exists in list of projects
                            exists_project = (path in [project["path"] for project in projects]) and \
                                (os.path.basename(path) in [project["name"] for project in projects])
                            if query_str in normalize_string(path) and not exists_project:
                                    projects.append({
                                        "name": os.path.basename(path),
                                        "path": path,
                                        "type": "Project/Folder" if entry.get("folderUri", "") else "File",
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
                                    if uri.startswith("file://"):
                                        uri = uri.replace("file://", "")
                                        # Check if the File or Project/Folder exists in the operative system
                                        if sub_item.get("id", {}) == "openRecentFolder":
                                            exists_in_os = True if os.path.isdir(uri) else False
                                        elif sub_item.get("id", {}) == "openRecentFile":
                                            exists_in_os = True if os.path.isfile(uri) else False
                                        else:
                                            exists_in_os = False
                                        if not exists_in_os:
                                            continue
                                        # Check if project already exists in list of projects
                                        exists_project = (uri in [project["path"] for project in projects]) and \
                                            (os.path.basename(uri) in [project["name"] for project in projects])
                                        if (query_str in normalize_string(uri) and uri != "") and not exists_project:
                                                projects.append({
                                                    "name": os.path.basename(uri),
                                                    "path": uri,
                                                    "type": "Project/Folder" if sub_item.get("id", {}) == \
                                                    	"openRecentFolder" else "File",
                                                })
                except Exception as e:
                    warning(f"Error reading {json_path}: {e}")

        # Add projects to query results
        for project in projects:
            query.add(StandardItem(
                id=project["path"],
                text=project["name"],
                subtext= project["type"] + ": " + project["path"],
                iconUrls=[f"file:{Path(__file__).parent}/vscode.svg"],
                actions=[Action(
                    id="open",
                    text="Open in VS Code",
                    callable=lambda p=project["path"]: runDetachedProcess([EXEC, p]),
                )],
            ))
        # Add an item to open a new VS Code empty window
        query.add(StandardItem(
            id="code",
            text="New empty window",
            subtext= "Open a new VS Code empty window",
            iconUrls=[f"file:{Path(__file__).parent}/vscode.svg"],
            actions=[Action(
                id="open",
                text="Open in VS Code",
                callable=lambda p="-n": runDetachedProcess([EXEC, p]),
            )],
        ))
