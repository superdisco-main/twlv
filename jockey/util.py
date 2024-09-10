import os
import sys
import json
import requests
import urllib
import ffmpeg
from dotenv import find_dotenv, load_dotenv
from typing import TYPE_CHECKING, Any, Dict, List
from rich.padding import Padding
from rich.console import Console
from rich.json import JSON

TL_BASE_URL = "https://api.twelvelabs.io/v1.2/"
INDEX_URL = urllib.parse.urljoin(TL_BASE_URL, "indexes/")
REQUIRED_ENVIRONMENT_VARIABLES = set([
    "TWELVE_LABS_API_KEY",
    "HOST_PUBLIC_DIR",
    "LLM_PROVIDER"
])
AZURE_ENVIRONMENT_VARIABLES = set([
    "AZURE_OPENAI_ENDPOINT",
    "AZURE_OPENAI_API_KEY",
    "OPENAI_API_VERSION"
])
OPENAI_ENVIRONMENT_VARIABLES = set([
    "OPENAI_API_KEY"
])
ALL_JOCKEY_ENVIRONMENT_VARIABLES = REQUIRED_ENVIRONMENT_VARIABLES | AZURE_ENVIRONMENT_VARIABLES | OPENAI_ENVIRONMENT_VARIABLES


def parse_langchain_events_terminal(event: dict):
    """Used to parse events emitted from Jockey when called as an API."""
    console = Console()

    if event["event"] == "on_chat_model_stream":
        if isinstance(event["data"]["chunk"], dict):
            content = event["data"]["chunk"]["content"]
        else:
            content = event["data"]["chunk"].content
        
        if content and "instructor" in event["tags"]:
            console.print(f"[red]{content}", end="")
        elif content and "planner" in event["tags"]:
            console.print(f"[yellow]{content}", end="")
        elif content and "supervisor" in event["tags"]:
            console.print(f"[white]{content}", end="")
    elif event["event"] == "on_tool_start":
        tool = event["name"]
        console.print(Padding(f"[cyan]🏇 Using: {tool}", (1, 0, 0, 2)))
        console.print(Padding(f"[cyan]🏇 Inputs:", (0, 2)))
        console.print(Padding(JSON(json.dumps(event["data"]["input"]), indent=2), (1, 6)))
    elif event["event"] == "on_tool_end":
        tool = event["name"]
        console.print(Padding(f"[cyan]🏇 Finished Using: {tool}", (0, 2)))
        console.print(Padding(f"[cyan]🏇 Outputs:", (0, 2)))
        try:
            console.print(Padding(JSON(event["data"]["output"], indent=2), (1, 6)))
        except (json.decoder.JSONDecodeError, TypeError):
            console.print(Padding(str(event["data"]["output"]), (0, 6)))
    elif event["event"] == "on_chat_model_start":
        if "instructor" in event["tags"]:
            console.print(Padding(f"[red]🏇 Instructor: ", (1, 0)), end="")
        elif "planner" in event["tags"]:
            console.print(Padding(f"[yellow]🏇 Planner: ", (1, 0)), end="")
        elif "reflect" in event["tags"]:
            console.print()
            console.print(f"[cyan]🏇 Jockey: ", end="")


def get_video_metadata(index_id: str, video_id: str) -> dict:
    video_url = f"{INDEX_URL}{index_id}/videos/{video_id}"

    headers = {
        "accept": "application/json",
        "Content-Type": "application/json",
        "x-api-key": os.environ["TWELVE_LABS_API_KEY"]
    }

    response = requests.get(video_url, headers=headers)

    try:
        assert response.status_code == 200
    except AssertionError:
        error_response = {
                "message": f"There was an error getting the metadata for Video ID: {video_id} in Index ID: {index_id}. "
                "Double check that the Video ID and Index ID are valid and correct.",
                "error": response.text
            }
        return error_response

    return response


def download_video(video_id: str, index_id: str, start: float, end: float) -> str:
    """Download a video for a given video in a given index and get the filepath. 
    Should only be used when the user explicitly requests video editing functionalities."""
    headers = {
        "x-api-key": os.environ["TWELVE_LABS_API_KEY"],
        "accept": "application/json",
        "Content-Type": "application/json"
    }

    video_url = f"https://api.twelvelabs.io/v1.2/indexes/{index_id}/videos/{video_id}"

    response = requests.get(video_url, headers=headers)
        
    assert response.status_code == 200

    hls_uri = response.json()["hls"]["video_url"]

    video_dir = os.path.join(os.environ["HOST_PUBLIC_DIR"], index_id)

    if os.path.isdir(video_dir) is False:
        os.mkdir(video_dir)

    video_filename = f"{video_id}_{start}_{end}.mp4"
    video_path = os.path.join(video_dir, video_filename)

    if os.path.isfile(video_path) is False:
        try:
            duration = end - start
            buffer = 1  # Add a 1-second buffer on each side
            ffmpeg.input(filename=hls_uri, strict="experimental", loglevel="quiet", ss=max(0, start-buffer), t=duration+2*buffer) \
                .output(video_path, vcodec="libx264", acodec="aac", avoid_negative_ts="make_zero", fflags="+genpts") \
                .run()

            # Then trim the video more precisely
            output_trimmed = f"{os.path.splitext(video_path)[0]}_trimmed.mp4"
            ffmpeg.input(video_path, ss=buffer, t=duration) \
                .output(output_trimmed, vcodec="copy", acodec="copy") \
                .run()

            # Replace the original file with the trimmed version
            os.replace(output_trimmed, video_path)
        except Exception as error:
            error_response = {
                "message": f"There was an error downloading the video with Video ID: {video_id} in Index ID: {index_id}. "
                "Double check that the Video ID and Index ID are valid and correct.",
                "error": str(error)
            }
            return error_response

    return video_path


def check_environment_variables():
    """Check that a .env file contains the required environment variables.
    Uses the current working directory tree to search for a .env file."""
    # Assume the .env file is someone on the current working directory tree.
    load_dotenv(find_dotenv(usecwd=True))

    if REQUIRED_ENVIRONMENT_VARIABLES & os.environ.keys() != REQUIRED_ENVIRONMENT_VARIABLES:
        missing_environment_variables = REQUIRED_ENVIRONMENT_VARIABLES - os.environ.keys()
        print(f"Expected the following environment variables:\n\t{str.join(', ', REQUIRED_ENVIRONMENT_VARIABLES)}")
        print(f"Missing:\n\t{str.join(', ', missing_environment_variables)}")
        sys.exit("Missing required environment variables.")

    if AZURE_ENVIRONMENT_VARIABLES & os.environ.keys() != AZURE_ENVIRONMENT_VARIABLES and \
        OPENAI_ENVIRONMENT_VARIABLES & os.environ.keys() != OPENAI_ENVIRONMENT_VARIABLES:
        missing_azure_environment_variables = AZURE_ENVIRONMENT_VARIABLES - os.environ.keys()
        missing_openai_environment_variables = OPENAI_ENVIRONMENT_VARIABLES - os.environ.keys()
        print(f"If using Azure, Expected the following environment variables:\n\t{str.join(', ', AZURE_ENVIRONMENT_VARIABLES)}")
        print(f"Missing:\n\t{str.join(', ', missing_azure_environment_variables)}")

        print(f"If using Open AI, Expected the following environment variables:\n\t{str.join(', ', OPENAI_ENVIRONMENT_VARIABLES)}")
        print(f"Missing:\n\t{str.join(', ', missing_openai_environment_variables)}")
        sys.exit("Missing Azure or Open AI environment variables.")

