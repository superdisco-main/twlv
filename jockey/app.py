import os
import sys
from typing import Union
from langchain_openai import AzureChatOpenAI, ChatOpenAI
from jockey.jockey_graph import Jockey, build_jockey_graph
from jockey.util import check_environment_variables


def build_jockey(
        planner_llm: Union[AzureChatOpenAI, ChatOpenAI], 
        supervisor_llm: Union[AzureChatOpenAI, ChatOpenAI], 
        worker_llm: Union[AzureChatOpenAI, ChatOpenAI]) -> Jockey:
    """Convenience function for standing up a local Jockey instance for dev work. 

    Args:
        planner_llm (Union[BaseChatOpenAI  |  AzureChatOpenAI]): 
            The LLM used for the planner node. It is recommended this be a GPT-4 class LLM.

        supervisor_llm (Union[BaseChatOpenAI  |  AzureChatOpenAI]): 
            The LLM used for the supervisor. It is recommended this be a GPT-4 class LLM or better.

        worker_llm (Union[BaseChatOpenAI  |  AzureChatOpenAI]): 
            The LLM used for the planner node. It is recommended this be a GPT-3.5 class LLM or better.

    Returns:
        Jockey: A local Jockey instance.
    """
    
    # Here we load all the required prompts for a Jockey instance.
    supervisor_filepath = os.path.join(os.path.dirname(__file__), "prompts", "supervisor.md")
    planner_filepath = os.path.join(os.path.dirname(__file__), "prompts", "planner.md")

    with open(supervisor_filepath, "r") as supervisor_prompt_file:
        supervisor_prompt = supervisor_prompt_file.read()

    with open(planner_filepath, "r") as planner_prompt_file:
        planner_prompt = planner_prompt_file.read()

    return build_jockey_graph(
        planner_llm=planner_llm,
        planner_prompt=planner_prompt, 
        supervisor_llm=supervisor_llm, 
        supervisor_prompt=supervisor_prompt,
        worker_llm=worker_llm
    )

# Here we construct all the LLMs for a Jockey instance.
# Currently we only support OpenAI LLMs
# Also note the class of LLM used for each component.
# When implementing your own server you can import build_jockey separately or modify this file directly.
# This allows you to choose your own LLMs.
check_environment_variables()


if os.environ["LLM_PROVIDER"] == "AZURE":
    planner_llm = AzureChatOpenAI(
        deployment_name="gpt-4",
        streaming=True,
        temperature=0,
        model_version="1106-preview",
        tags=["planner"]
    )

    supervisor_llm = AzureChatOpenAI(
        deployment_name="gpt-4",
        streaming=True,
        temperature=0,
        model_version="1106-preview",
        tags=["supervisor"]
    )

    worker_llm = AzureChatOpenAI(
        deployment_name="gpt-35-turbo-16k",
        streaming=True,
        temperature=0,
        model_version="0613",
        tags=["worker"]
    )
elif os.environ["LLM_PROVIDER"] == "OPENAI":
    planner_llm = ChatOpenAI(
        model="gpt-4o",
        streaming=True,
        temperature=0,
        tags=["planner"]
    )

    supervisor_llm = ChatOpenAI(
        model="gpt-4o",
        streaming=True,
        temperature=0,
        tags=["supervisor"]
    )

    worker_llm = ChatOpenAI(
        model="gpt-4o-mini-2024-07-18",
        streaming=True,
        temperature=0,
        tags=["worker"]
    )
else:
    print(f"LLM_PROVIDER environment variable is incorrect. Must be one of: [AZURE, OPENAI] but got {os.environ['LLM_PROVIDER']}")
    sys.exit("Incorrect LLM_PROVIDER environment variable.")

# This variable is what is used by the LangGraph API server.
jockey = build_jockey(planner_llm=planner_llm, supervisor_llm=supervisor_llm, worker_llm=worker_llm)
