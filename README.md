# Getting Started with Jockey Chat
<img width="1522" alt="Screenshot 2024-02-16 at 4 27 12 PM" src="https://github.com/twelvelabs-io/tl-jockey/assets/101737790/45755337-c024-422c-a538-786f08ed98f8">

## Table of Contents
- [About](#about)
- [Installation](#installation)
- [Navigation](#navigation)
  - [servers](#servers)
  - [main_components](#main_components)
- [License](#license)
- [Links](#links)

## About

### `Web services`
We are using Vercel web services to deploy this project

### `Tech stack`
TypeScript, JavaScript, React, Tailwind CSS, Python, Pandas, Heroku, Ngrok 

### `Python dependencies requirements`
pandas==2.0.3
ffmpeg-python==0.2.0
pytube==15.0.0
grequests==0.7.0
m3u8-To-MP4==0.1.11
langchain==0.1.4
langchain-experimental==0.0.49
tabulate==0.9.0
certifi==2023.11.17
python-dotenv==1.0.1
openai==1.10.0
langchain-openai==0.0.4
rich==13.7.0
fastapi==0.110.0
uvicorn==0.28.0
langserve==0.0.51
sse-starlette==2.0.0
httpx-sse==0.4.0

## What's inside?

This project includes the following applications and packages

### Apps
- [JockeyChat]
- [JockeyML]

### Functionality Overview

Additionally, the components within this repository are divided into two distinct packets: components and widgets, based on their intended usage. 


## Installation
# Commands
Install all required packages using Yarn. Run the following commands
### `yarn install`

To start the project

### `yarn start`

## Navigation
### Servers
The structure of the project is divided into several key components: the frontend, the proxy server, and the LangGraph server. The goal is to provide a seamless interaction between the user interface and the LangGraph server, facilitated by the proxy server for better manageability

Frontend
The frontend is responsible for the user interface and user interactions. It communicates with the LangChain server via a proxy server.

Proxy Server
The proxy server acts as an intermediary between the frontend and the LangGraph server. It ensures secure and efficient communication, handles requests from the frontend, and forwards them to the LangGraph server. The proxy server is initially set up in the apiConfig => ProxyServer file. If you need to create a new proxy server or modernize the existing one, you can refer to the 'launch' component inside the Jockey folder and 'server' component in the source. These components includes all the streaming functionality required for communication with the LangGraph server. 

LangGraph Server 
The LangGraph server is the backend component that processes the logic and data required for the application. It receives requests from the proxy server, processes them, and returns the necessary responses. All of the components related to this functionality located into the Jockey folder with a solid README regarding how to launch, test and modernise the functianality  

###Main_components 
All API calls related to these components are defined in the api folder, where the hooks file is located. 
- api/: Contains API-related files. 
- hooks.js: Defines hooks for making API calls (for the TwelveLabs api's) 
- apiConfig.js: Defines or creates URL paths and keys for React Query. 
- streamEventsApis.js: Contains all APIs for making calls to the proxy server. 

###Build and deploy 
Build and deploy 
This project uses Vercel to ship application on the internet.
For production environment  we use Vercel's default configuration to deploy preview and production app.
Ask the team for an invitation to be added as a member of Twelve Labs Team.

##Links
- [Web site](https://www.twelvelabs.io)
- [Documentation](https://github.com/twelvelabs-io/tl-jockey/blob/main/README.md)
- [Source code](https://github.com/twelvelabs-io/tl-jockey/tree/main)

