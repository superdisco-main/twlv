import requests
import json
import urllib
import os
from pydantic import BaseModel, Field
from langchain.tools import tool
from typing import Dict, List, Union
from enum import Enum
from jockey.video_utils import get_video_metadata
from jockey.prompts import DEFAULT_VIDEO_TEXT_GENERATION_FILE_PATH
from jockey.stirrups.stirrup import Stirrup
from jockey.stirrups.errors import ErrorType, JockeyError, NodeType, WorkerFunction, create_jockey_error_event


TL_BASE_URL = "https://api.twelvelabs.io/v1.3/"
GIST_URL = urllib.parse.urljoin(TL_BASE_URL, "gist")
SUMMARIZE_URL = urllib.parse.urljoin(TL_BASE_URL, "summarize")
GENERATE_URL = urllib.parse.urljoin(TL_BASE_URL, "generate")


class GistEndpointsEnum(str, Enum):
    """Helps to ensure the video-text-generation worker selects valid `endpoint` options for the gist tool."""

    TOPIC = "topic"
    HASHTAG = "hashtag"
    TITLE = "title"


class SummarizeEndpointEnum(str, Enum):
    """Helps to ensure the video-text-generation worker selects a valid `endpoint_option` for the summarize tool."""

    SUMMARY = "summary"
    HIGHLIGHT = "highlight"
    CHAPTER = "chapter"


class PegasusGistInput(BaseModel):
    """Help to ensure the video-text-generation worker provides valid arguments to any tool it calls."""

    video_id: str = Field(description="The ID of the video to generate text from.")
    index_id: str = Field(description="Index ID which contains a collection of videos.")
    endpoint_options: List[GistEndpointsEnum] = Field(description="Determines what outputs to generate.")


class PegasusSummarizeInput(BaseModel):
    """Help to ensure the video-text-generation worker provides valid arguments to any tool it calls."""

    video_id: str = Field(description="The ID of the video to generate text from.")
    index_id: str = Field(description="Index ID which contains a collection of videos.")
    endpoint_option: SummarizeEndpointEnum = Field(description="Determines what output to generate.")
    prompt: Union[str, None] = Field(
        description="Instructions on how summaries, highlights, and chapters are generated. " "Always use when additional context is provided.",
        max_length=300,
    )


class VideoTextGenerationInput(BaseModel):
    """Schema for video-text-generation worker that is compatible with OpenAI API response_format."""

    video_id: str = Field(description="The ID of the video to generate text from.")
    index_id: str = Field(description="Index ID which contains a collection of videos.")
    endpoint_option: SummarizeEndpointEnum = Field(
        description="Determines what output to generate.",
        default=SummarizeEndpointEnum.SUMMARY
    )
    prompt: Union[str, None] = Field(
        description="Instructions on how summaries, highlights, and chapters are generated. Always use when additional context is provided.",
        default=None
    )


class PegasusFreeformInput(BaseModel):
    """Help to ensure the video-text-generation worker provides valid arguments to any tool it calls."""

    video_id: str = Field(description="The ID of the video to generate text from.")
    index_id: str = Field(description="Index ID which contains a collection of videos.")
    prompt: str = Field(
        description="Instructions on what text output to generate. Can be anything. " "Always use when additional context is provided.",
        max_length=300,
    )


@tool("gist-text-generation", args_schema=PegasusGistInput)
async def gist_text_generation(video_id: str, index_id: str = None, endpoint_options: List[GistEndpointsEnum] = None) -> Dict:
    """Generate `gist` output for a single video. This can include any combination of: topics, hashtags, and a title"""
    try:
        headers = {"accept": "application/json", "x-api-key": os.environ["TWELVE_LABS_API_KEY"], "Content-Type": "application/json"}
        
        # 기본값 설정
        if endpoint_options is None:
            endpoint_options = [GistEndpointsEnum.TOPIC, GistEndpointsEnum.HASHTAG, GistEndpointsEnum.TITLE]
            
        payload = {"video_id": video_id, "types": endpoint_options}

        # API 호출
        response = requests.post(GIST_URL, json=payload, headers=headers)
        response = response.json()
        
        # 비디오 메타데이터 가져오기 (선택적)
        if index_id:
            try:
                video_metadata = get_video_metadata(index_id=index_id, video_id=video_id)
                # Add video_url if available
                try:
                    # 응답 객체인 경우
                    if hasattr(video_metadata, 'json'):
                        metadata_dict = video_metadata.json()
                    # 이미 딕셔너리인 경우
                    else:
                        metadata_dict = video_metadata
                    
                    if "hls" in metadata_dict and "video_url" in metadata_dict["hls"]:
                        response["video_url"] = metadata_dict["hls"]["video_url"]
                    else:
                        response["video_url"] = "Video URL not available in metadata"
                except (AttributeError, KeyError) as e:
                    response["video_url"] = f"Error getting video URL: {str(e)}"
            except Exception as e:
                response["video_url"] = f"Error getting video metadata: {str(e)}"
            
        return json.dumps(response)

    except Exception as error:
        jockey_error = JockeyError.create(
            node=NodeType.WORKER,
            error_type=ErrorType.TEXT_GENERATION,
            function_name=WorkerFunction.GIST_TEXT_GENERATION,
            details=f"Error: {str(error)}",
        )
        raise jockey_error


@tool("summarize-text-generation", args_schema=PegasusSummarizeInput)
async def summarize_text_generation(video_id: str, index_id: str = None, endpoint_option: SummarizeEndpointEnum = SummarizeEndpointEnum.SUMMARY, prompt: Union[str, None] = None) -> Dict:
    """Generate `summary` `highlight` or `chapter` for a single video.
    
    - summary: A brief that encapsulates the key points of a video, presenting the most important information clearly and concisely.
    - chapter: A chronological list of all the chapters in a video, providing a granular breakdown of its content.
    - highlight: A chronologically ordered list of the most important events within a video.
    """
    try:
        headers = {"accept": "application/json", "x-api-key": os.environ["TWELVE_LABS_API_KEY"], "Content-Type": "application/json"}
        payload = {
            "video_id": video_id,
            "type": endpoint_option,
        }
        
        # 요약 유형에 따라 기본 프롬프트 설정
        if prompt is None:
            if endpoint_option == SummarizeEndpointEnum.SUMMARY:
                prompt = "Generate a concise summary of the video content, highlighting the main points and key information."
            elif endpoint_option == SummarizeEndpointEnum.CHAPTER:
                prompt = "Divide the video into logical chapters, providing a title and brief summary for each chapter."
            elif endpoint_option == SummarizeEndpointEnum.HIGHLIGHT:
                prompt = "Identify the most important moments in the video and provide a brief description for each highlight."
        
        if prompt is not None:
            payload["prompt"] = prompt

        # API 호출
        response = requests.post(SUMMARIZE_URL, json=payload, headers=headers)
        response = response.json()
        
        # 비디오 메타데이터 가져오기 (선택적)
        if index_id:
            try:
                video_metadata = get_video_metadata(index_id=index_id, video_id=video_id)
                # Add video_url if available
                try:
                    # 응답 객체인 경우
                    if hasattr(video_metadata, 'json'):
                        metadata_dict = video_metadata.json()
                    # 이미 딕셔너리인 경우
                    else:
                        metadata_dict = video_metadata
                    
                    if "hls" in metadata_dict and "video_url" in metadata_dict["hls"]:
                        response["video_url"] = metadata_dict["hls"]["video_url"]
                    else:
                        response["video_url"] = "Video URL not available in metadata"
                except (AttributeError, KeyError) as e:
                    response["video_url"] = f"Error getting video URL: {str(e)}"
            except Exception as e:
                response["video_url"] = f"Error getting video metadata: {str(e)}"
            
        return json.dumps(response)

    except Exception as error:
        jockey_error = JockeyError.create(
            node=NodeType.WORKER,
            error_type=ErrorType.TEXT_GENERATION,
            function_name=WorkerFunction.SUMMARIZE_TEXT_GENERATION,
            details=f"Error: {str(error)}",
        )
        raise jockey_error


@tool("freeform-text-generation", args_schema=PegasusFreeformInput)
async def freeform_text_generation(video_id: str, index_id: str = None, prompt: str = "") -> Dict:
    """Generate any type of text output for a single video.
    Useful for answering specific questions, understanding fine grained details, and anything else that doesn't fall neatly into the other tools."""
    try:
        headers = {"accept": "application/json", "x-api-key": os.environ["TWELVE_LABS_API_KEY"], "Content-Type": "application/json"}
        payload = {
            "video_id": video_id,
            "prompt": prompt,
        }

        # API 호출
        response = requests.post(GENERATE_URL, json=payload, headers=headers)
        response = response.json()
        
        # 비디오 메타데이터 가져오기 (선택적)
        if index_id:
            try:
                video_metadata = get_video_metadata(index_id=index_id, video_id=video_id)
                # Add video_url if available
                try:
                    # 응답 객체인 경우
                    if hasattr(video_metadata, 'json'):
                        metadata_dict = video_metadata.json()
                    # 이미 딕셔너리인 경우
                    else:
                        metadata_dict = video_metadata
                    
                    if "hls" in metadata_dict and "video_url" in metadata_dict["hls"]:
                        response["video_url"] = metadata_dict["hls"]["video_url"]
                    else:
                        response["video_url"] = "Video URL not available in metadata"
                except (AttributeError, KeyError) as e:
                    response["video_url"] = f"Error getting video URL: {str(e)}"
            except Exception as e:
                response["video_url"] = f"Error getting video metadata: {str(e)}"
            
        return json.dumps(response)

    except Exception as error:
        jockey_error = JockeyError.create(
            node=NodeType.WORKER,
            error_type=ErrorType.TEXT_GENERATION,
            function_name=WorkerFunction.FREEFORM_TEXT_GENERATION,
            details=f"Error: {str(error)}",
        )
        raise jockey_error


# Construct a valid worker for a Jockey instance.
video_text_generation_worker_config = {
    "tools": [gist_text_generation, summarize_text_generation, freeform_text_generation],
    "worker_prompt_file_path": DEFAULT_VIDEO_TEXT_GENERATION_FILE_PATH,
    "worker_name": "video-text-generation",
}
VideoTextGenerationWorker = Stirrup(**video_text_generation_worker_config)
