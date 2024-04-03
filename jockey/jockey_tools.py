import urllib
import requests
import os
import ffmpeg
from langchain.tools import tool
from langchain.pydantic_v1 import BaseModel, Field
from typing import List, Dict, Union
from util import get_video_metadata


TL_BASE_URL = "https://api.twelvelabs.io/v1.2/"
INDEX_URL = urllib.parse.urljoin(TL_BASE_URL, "indexes/")
EXTERNAL_UPLOAD_URL = urllib.parse.urljoin(TL_BASE_URL, "tasks/external-provider/")
SEARCH_URL = urllib.parse.urljoin(TL_BASE_URL, "search/")
GIST_URL = urllib.parse.urljoin(TL_BASE_URL, "gist/")
SUMMARIZE_URL = urllib.parse.urljoin(TL_BASE_URL, "summarize/")
GENERATE_URL = urllib.parse.urljoin(TL_BASE_URL, "generate/")

PEGASUS_INDEX_ID = "659ecd3e6bb8e7df9af19eaa"
MARENGO_INDEX_ID = "659f2e829aba4f0b402f6488"

class MarengoSearchInput(BaseModel):
    query: str = Field(description="Search query to run on a collection of videos.")
    index_id: str = Field(description="Index ID which contains a collection of videos.")
    top_n: int = Field(description="Used to select the top N results of a search.", gt=0, le=10)
    group_by: str = Field(description="Used to decide how to group search results. Must be one of: `clip` or `video`.")


@tool("video-search", args_schema=MarengoSearchInput)
async def video_search(query: str, index_id: str, top_n: int = 3, group_by: str = "clip") -> Union[List[Dict], List]:
    """Run a search query against a collection of videos and get results."""
    headers = {
        "x-api-key": os.environ["TWELVE_LABS_API_KEY"],
        "accept": "application/json",
        "Content-Type": "application/json"
    }

    payload = {
        "search_options": ["visual", "conversation"],
        "group_by": group_by,
        "threshold": "low",
        "sort_option": "score",
        "operator": "or",
        "conversation_option": "semantic",
        "page_limit": top_n,
        "index_id": index_id,
        "query": query
    }

    response = requests.post(SEARCH_URL, json=payload, headers=headers)

    if response.status_code != 200:
        error_response = {
            "message": "There was an API error when searching the index.",
            "url": SEARCH_URL,
            "headers": headers,
            "json_payload": payload,
            "response": response.text
        }
        return error_response

    if group_by == "video":
        top_n_results = [{"video_id": video["id"]} for video in response.json()["data"][:top_n]]
    else:
        top_n_results = response.json()["data"][:top_n]

    for result in top_n_results:
        video_id = result["video_id"]

        response = get_video_metadata(video_id=video_id, index_id=index_id)

        if response.status_code != 200:
            error_response = {
                "message": "There was an API error when retrieving video metadata.",
                "video_id": video_id,
                "response": response.text
            }
            return error_response
        
        result["video_url"] = response.json()["hls"]["video_url"]

        if group_by == "video":
            result["thumbnail_url"] = response.json()["hls"]["thumbnail_urls"][0]

    return top_n_results


class DownloadVideoInput(BaseModel):
    video_id: str = Field(description="Video ID used to download a video. It is also used as the filename for the video.")
    index_id: str = Field(description="Index ID which contains a collection of videos.")


@tool("video-download", args_schema=DownloadVideoInput)
def download_video(video_id: str, index_id: str) -> str:
    """Download a video for a given video in a given index and get the filepath. 
    Should only be used when the user explicitly requests video editing functionalities."""
    headers = {
        "x-api-key": os.environ["TWELVE_LABS_API_KEY"],
        "accept": "application/json",
        "Content-Type": "application/json"
    }

    video_url = f"https://api.twelvelabs.io/v1.2/indexes/{MARENGO_INDEX_ID}/videos/{video_id}"

    response = requests.get(video_url, headers=headers)

    hls_uri = response.json()["hls"]["video_url"]

    video_dir = os.path.join(os.getcwd(), index_id)
    video_filename = f"{video_id}.mp4"
    video_path = os.path.join(video_dir, video_filename)

    if os.path.isfile(video_path) is False:
        try:
            ffmpeg.input(filename=hls_uri, strict="experimental", loglevel="quiet").output(video_path, vcodec="copy", acodec="libmp3lame").run()
        except Exception as error:
            error_response = {
                "message": "There was a video editing error.",
                "error": error
            }
            return error_response

    return video_path


class CombineClipsInput(BaseModel):
    clips: List = Field(description="""Clip results found using the video-search tool.""")
    queries: List[str] = Field(description="The search queries passed to the video-search tool to find the clips. One for each clip.")
    output_filename: str = Field(description="The output filename of the combined clips. Must be in the form: [filename].mp4")
    index_id: str = Field(description="Index ID the clips belong to.")


@tool("combine-clips", args_schema=CombineClipsInput)
def combine_clips(clips: List[Dict], queries: List[str], output_filename: str, index_id: str) -> str:
    """Combine or edit multiple clips together based on video IDs that are results from the video-search tool. The full filepath for the combined clips is returned."""
    try:
        input_streams = []
        arial_font_file = os.path.join(os.getcwd(), "assets", "fonts", "Arial.ttf")

        for clip, query in zip(clips, queries):
            video_id = clip["video_id"]
            video_filepath = os.path.join(os.getcwd(), index_id, f"{video_id}.mp4")
            start = clip["start"]
            end = clip["end"]

            video_input_stream = ffmpeg.input(filename=video_filepath, loglevel="quiet").video.filter("trim", start=start, end=end).filter("setpts", "PTS-STARTPTS")
            audio_input_stream = ffmpeg.input(filename=video_filepath, loglevel="quiet").audio.filter("atrim", start=start, end=end).filter("asetpts", "PTS-STARTPTS")
            clip_with_text_stream = video_input_stream.drawtext(text=query, x="(w-text_w)/2", fontfile=arial_font_file, box=1, 
                                                                boxcolor="black", fontcolor="white", fontsize=28)
            
            input_streams.append(clip_with_text_stream)
            input_streams.append(audio_input_stream)

        output_filepath = os.path.join(os.getcwd(), index_id, output_filename)
        ffmpeg.concat(*input_streams, v=1, a=1).output(output_filepath, acodec="libmp3lame").overwrite_output().run()

        return output_filepath
    except Exception as error:
        error_response = {
            "message": "There was a video editing error.",
            "error": error
        }
        return error_response


class RemoveSegmentInput(BaseModel):
    video_filepath: str = Field(description="Full path to target video file.")
    start: float = Field(description="""Start time of segment to be removed. Must be in the format of: seconds.milliseconds""")
    end: float = Field(description="""End time of segment to be removed. Must be in the format of: seconds.milliseconds""")


@tool("remove-segment", args_schema=RemoveSegmentInput)
def remove_segment(video_filepath: str, start: float, end: float) -> str:
    """Remove a segment from a video at specified start and end times The full filepath for the edited video is returned."""
    output_filepath = f"{os.path.splitext(video_filepath)[0]}_clipped.mp4"

    left_cut_video_stream = ffmpeg.input(filename=video_filepath, loglevel="quiet").video.filter("trim", start=0, end=start).filter("setpts", "PTS-STARTPTS")
    left_cut_audio_stream = ffmpeg.input(filename=video_filepath, loglevel="quiet").audio.filter("atrim", start=0, end=start).filter("asetpts", "PTS-STARTPTS")
    right_cut_video_stream = ffmpeg.input(filename=video_filepath, loglevel="quiet").video.filter("trim", start=end).filter("setpts", "PTS-STARTPTS")
    right_cut_audio_stream = ffmpeg.input(filename=video_filepath, loglevel="quiet").audio.filter("atrim", start=end).filter("asetpts", "PTS-STARTPTS")

    streams = [left_cut_video_stream, left_cut_audio_stream, right_cut_video_stream, right_cut_audio_stream]

    ffmpeg.concat(*streams, v=1, a=1).output(filename=output_filepath, acodec="libmp3lame").overwrite_output().run()

    return output_filepath


class PegasusGenerateInput(BaseModel):
    video_id: str = Field(description="The ID of the video to generate text from.")
    endpoint: str = Field(description="""What type of text to generate from a video: must be one of: ['gist', 'summarize', 'generate']
                                      gist: For topics, titles, and hashtags using predefined formats.
                                      summarize: For summaries, chapters, and highlights, allowing customization with a prompt
                                      generate: For open-ended text, requiring clear instructions in the form of a prompt to guide the output.""")
    prompt: str = Field(default=None, description="The prompt to be used when generating output for a certain task. Only required for the 'generate' endpoint and optional for the 'summarize' endpoint.")
    endpoint_options: Union[str, List[str]] = Field(default=None, description="""Determines what the user wishes to generate. For the 'summarize' endpoint must be exactly one of: ['summary', 'highlight', 'chapter'].
                                                                              For the 'gist' endpoint can be any combination of: ['topic', 'hashtag', 'title'].""")


@tool("video-text-generation", args_schema=PegasusGenerateInput)
def video_text_generation(video_id: str, endpoint: str, prompt: str = None, endpoint_options: Union[str, List[str]] = None):
    """Generate text output for a single video. The text generated can have various options depending on the user's request."""

    headers = {
            "accept": "application/json",
            "x-api-key": os.environ["TWELVE_LABS_API_KEY"],
            "Content-Type": "application/json"
        }
    
    payload = {
        "video_id": video_id
    }

    url = None

    if endpoint == "gist":
        url = GIST_URL

        if endpoint_options is not None:
            payload["types"] = endpoint_options
    elif endpoint == "summarize":
        url = SUMMARIZE_URL

        if endpoint_options is not None:
            payload["type"] = endpoint_options
    elif endpoint == "generate":
        url = GENERATE_URL

    if prompt is not None:
        payload["prompt"] = prompt

    response = requests.post(url, json=payload, headers=headers)

    return response.json()

JOCKEY_TOOLKIT = [video_search, download_video, combine_clips, remove_segment, video_text_generation]
