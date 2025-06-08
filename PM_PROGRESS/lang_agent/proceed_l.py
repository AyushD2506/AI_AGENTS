import os
import re
import json
from datetime import datetime, timedelta
from typing import TypedDict, List, Optional, Dict, Any
from dataclasses import dataclass
import base64
from pathlib import Path
import hashlib
import shutil

from langgraph.graph import StateGraph, END
from langchain_groq import ChatGroq
from langchain.schema import HumanMessage, SystemMessage
from langchain.prompts import ChatPromptTemplate

GROQ_API_KEY = "YOUR_API_KEY"
MODEL_NAME = "meta-llama/llama-4-scout-17b-16e-instruct"
VISION_MODEL_NAME = "meta-llama/llama-4-scout-17b-16e-instruct"  

@dataclass
class ProjectData:
    name: str
    description: str
    user_input: str
    images: List[str]  
    log_file_path: str
    json_file_path: str
    username: str
    current_date: str  

class AgentState(TypedDict):
    project_data: ProjectData
    previous_logs: List[Dict[str, Any]]
    current_log: Optional[str]
    image_analyses: List[Dict[str, Any]]
    previous_images: List[str]  
    error: Optional[str]

class ProjectProgressAgent:
    def __init__(self, groq_api_key: str):
        self.llm = ChatGroq(
            groq_api_key=groq_api_key,
            model_name=MODEL_NAME,
            temperature=0.3,
            max_tokens=2048
        )
        self.vision_llm = ChatGroq(
            groq_api_key=groq_api_key,
            model_name=VISION_MODEL_NAME,
            temperature=0.3,
            max_tokens=2048
        )
        self.graph = self._build_graph()
    
    def _build_graph(self) -> StateGraph:
        workflow = StateGraph(AgentState)
        
        
        workflow.add_node("load_previous_logs", self._load_previous_logs)
        workflow.add_node("analyze_images", self._analyze_images)
        workflow.add_node("analyze_progress", self._analyze_progress)
        workflow.add_node("generate_log", self._generate_log)
        workflow.add_node("save_to_files", self._save_to_files)
        
        workflow.set_entry_point("load_previous_logs")
        workflow.add_edge("load_previous_logs", "analyze_images")
        workflow.add_edge("analyze_images", "analyze_progress")
        workflow.add_edge("analyze_progress", "generate_log")
        workflow.add_edge("generate_log", "save_to_files")
        workflow.add_edge("save_to_files", END)
        
        return workflow.compile()
    
    def _create_directory_structure(self, username: str) -> tuple:
        base_dir = Path("data")
        log_dir = base_dir / "log"
        user_dir = log_dir / username
        
        user_dir.mkdir(parents=True, exist_ok=True)
        
        assets_dir = user_dir / "assets"
        assets_dir.mkdir(exist_ok=True)
        
        json_file = user_dir / f"{username}_logs.json"
        md_file = user_dir / f"{username}_logs.md"
        
        return str(json_file), str(md_file), str(assets_dir)
    
    def _encode_image_to_base64(self, image_path: str) -> str:
        try:
            with open(image_path, "rb") as image_file:
                return base64.b64encode(image_file.read()).decode('utf-8')
        except Exception as e:
            print(f"Error encoding image {image_path}: {str(e)}")
            return ""
    
    def _get_image_hash(self, image_path: str) -> str:
        try:
            with open(image_path, "rb") as f:
                return hashlib.md5(f.read()).hexdigest()
        except:
            return ""
    
    def _copy_image_to_assets(self, image_path: str, username: str, current_date: str) -> tuple:
        try:
            _, _, assets_dir = self._create_directory_structure(username)
            assets_path = Path(assets_dir)
            
            image_name = Path(image_path).name
            clean_name = re.sub(r'[^\w\-_\.]', '_', image_name)
            new_name = f"{current_date}_{clean_name}"
            
            dest_path = assets_path / new_name
            shutil.copy2(image_path, dest_path)
            
            relative_path = f"./assets/{new_name}"
            return str(dest_path), relative_path
        except Exception as e:
            print(f"Error copying image: {str(e)}")
            return image_path, image_path
    
    def _load_previous_logs(self, state: AgentState) -> AgentState:
        try:
            json_file_path = state["project_data"].json_file_path
            
            if not os.path.exists(json_file_path):
                state["previous_logs"] = []
                state["previous_images"] = []
                return state
            
            with open(json_file_path, 'r', encoding='utf-8') as file:
                data = json.load(file)
            
            logs = []
            previous_images = []
            
            for date_str, log_content in data.items():
                image_pattern = r'!\[.*?\]\((.*?)\)'
                images_in_log = re.findall(image_pattern, log_content)
                previous_images.extend(images_in_log)
                
                logs.append({
                    'date': date_str,
                    'content': log_content,
                    'images': images_in_log
                })
            
            logs.sort(key=lambda x: x['date'], reverse=True)
            state["previous_logs"] = logs[:5]
            state["previous_images"] = list(set(previous_images)) 

            
        except Exception as e:
            state["error"] = f"Error loading previous logs: {str(e)}"
            state["previous_logs"] = []
            state["previous_images"] = []
        
        return state
    
    def _analyze_images(self, state: AgentState) -> AgentState:
        try:
            project_data = state["project_data"]
            image_analyses = []
            
            if not project_data.images:
                state["image_analyses"] = []
                return state
            
            for image_path in project_data.images:
                if not os.path.exists(image_path):
                    continue
                
                image_hash = self._get_image_hash(image_path)
                is_new_image = True  
                
                base64_image = self._encode_image_to_base64(image_path)
                if not base64_image:
                    continue
                
                analysis_prompt = f"""
                Analyze this image in the context of the project: {project_data.name}
                
                Project Description: {project_data.description}
                Today's Update: {project_data.user_input}
                
                Please provide:
                1. What does this image show?
                2. How does it relate to the project progress?
                3. What technical details or insights can you extract?
                4. Any issues, achievements, or notable elements visible?
                
                Keep the analysis concise but informative.
                """
                
                messages = [
                    SystemMessage(content="You are an expert at analyzing technical images and screenshots in the context of software development and project progress."),
                    HumanMessage(content=[
                        {"type": "text", "text": analysis_prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}"
                            }
                        }
                    ])
                ]
                
                response = self.vision_llm.invoke(messages)
                
                abs_path, relative_path = self._copy_image_to_assets(
                    image_path, project_data.username, project_data.current_date
                )
                
                image_analyses.append({
                    'path': image_path,
                    'absolute_path': abs_path,
                    'relative_path': relative_path,
                    'analysis': response.content,
                    'is_new': is_new_image,
                    'hash': image_hash
                })
            
            state["image_analyses"] = image_analyses
            
        except Exception as e:
            state["error"] = f"Error analyzing images: {str(e)}"
            state["image_analyses"] = []
        
        return state
    
    def _analyze_progress(self, state: AgentState) -> AgentState:
        try:
            project_data = state["project_data"]
            previous_logs = state["previous_logs"]
            image_analyses = state["image_analyses"]
            
            analysis_prompt = self._create_analysis_prompt(project_data, previous_logs, image_analyses)
            
            messages = [
                SystemMessage(content="""You are a project progress analysis expert. 
                Analyze the provided project data, previous logs, and image analysis to understand:
                1. Current progress status
                2. Visual evidence of progress from images
                3. Challenges faced
                4. Patterns in work
                5. Areas needing attention
                6. How the images support or contradict the text updates
                
                Provide concise, actionable insights that incorporate both text and visual information."""),
                HumanMessage(content=analysis_prompt)
            ]
            
            response = self.llm.invoke(messages)
            state["analysis"] = response.content
            
        except Exception as e:
            state["error"] = f"Error during analysis: {str(e)}"
        
        return state
    
    def _generate_log(self, state: AgentState) -> AgentState:
        try:
            project_data = state["project_data"]
            analysis = state.get("analysis", "")
            image_analyses = state["image_analyses"]
            current_date = project_data.current_date  # Use user-provided date
            
            log_prompt = self._create_log_generation_prompt(
                project_data, analysis, image_analyses, current_date
            )
            
            messages = [
                SystemMessage(content="""You are a professional project logger. 
                Create a comprehensive daily log entry in markdown format that includes both text and images.
                
                CRITICAL: You MUST include images in the markdown using the exact format provided.
                
                Structure your response as:
                ## YYYY-MM-DD
                
                ### Progress Summary
                [Brief overview of today's progress, mention visual evidence if images provided]
                
                ### Tasks Completed
                - [List completed tasks]
                
                ### Visual Evidence
                ![Alt Text](./assets/filename.ext)
                **Image Analysis:** [Detailed analysis of what the image shows]
                
                [Repeat for each image provided]
                
                ### Challenges Faced
                - [List any challenges or blockers]
                
                ### Next Steps
                - [List planned next actions]
                
                ### Notes
                [Any additional observations or insights]
                
                MANDATORY RULES:
                1. If images are provided, you MUST include a "Visual Evidence" section
                2. Use the exact image paths provided in the prompt
                3. Include detailed image analysis under each image
                4. Reference visual evidence in other sections when relevant
                5. Use proper markdown image syntax: ![Alt Text](path)
                
                Keep it professional, concise, and actionable."""),
                HumanMessage(content=log_prompt)
            ]
            
            response = self.llm.invoke(messages)
            
            log_content = response.content
            
            if image_analyses and "### Visual Evidence" not in log_content:
                sections = ["### Challenges Faced", "### Next Steps", "### Notes"]
                insert_before = None
                
                for section in sections:
                    if section in log_content:
                        insert_before = section
                        break
                
                image_section = "\n### Visual Evidence\n"
                for i, img_data in enumerate(image_analyses, 1):
                    alt_text = f"Project Screenshot {i} - {current_date}"
                    image_section += f"\n![{alt_text}]({img_data['relative_path']})\n\n"
                    
                    analysis_preview = img_data['analysis'][:300] + "..." if len(img_data['analysis']) > 300 else img_data['analysis']
                    image_section += f"**Image Analysis:** {analysis_preview}\n\n"
                
                if insert_before:
                    log_content = log_content.replace(insert_before, f"{image_section}\n{insert_before}")
                else:
                    log_content += f"\n{image_section}"
            
            state["current_log"] = log_content
            
        except Exception as e:
            state["error"] = f"Error generating log: {str(e)}"
        
        return state
    
    def _save_to_files(self, state: AgentState) -> AgentState:
        try:
            if state["current_log"]:
                project_data = state["project_data"]
                current_log = state["current_log"]
                current_date = project_data.current_date
                
                self._save_to_json(project_data.json_file_path, current_date, current_log)
                
                self._save_to_md(project_data.log_file_path, current_log)
                
                # self._create_html_preview(project_data.log_file_path, current_log)
                
                state["success"] = True
            
        except Exception as e:
            state["error"] = f"Error saving files: {str(e)}"
        
        return state
    
    def _save_to_json(self, json_file_path: str, current_date: str, log_content: str):
        try:
            data = {}
            if os.path.exists(json_file_path):
                with open(json_file_path, 'r', encoding='utf-8') as file:
                    try:
                        data = json.load(file)
                    except json.JSONDecodeError:
                        data = {}
            
            data[current_date] = log_content
            
            with open(json_file_path, 'w', encoding='utf-8') as file:
                json.dump(data, file, indent=2, ensure_ascii=False)
                
        except Exception as e:
            raise Exception(f"Error saving to JSON: {str(e)}")
    
    def _save_to_md(self, md_file_path: str, log_content: str):
        """Save log to MD file (append to existing content)"""
        try:
            existing_content = ""
            if os.path.exists(md_file_path):
                with open(md_file_path, 'r', encoding='utf-8') as file:
                    existing_content = file.read()
            
            separator = "\n\n---\n\n" if existing_content.strip() else ""
            
            new_content = f"{log_content}{separator}{existing_content}"
            
            with open(md_file_path, 'w', encoding='utf-8') as file:
                file.write(new_content)
                
        except Exception as e:
            raise Exception(f"Error saving to MD: {str(e)}")
    
    def _create_html_preview(self, log_file_path: str, content: str):
        try:
            html_path = log_file_path.replace('.md', '_preview.html')
            
            html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Project Log Preview</title>
    <style>
        body {{ font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }}
        img {{ max-width: 100%; height: auto; border: 1px solid #ddd; margin: 10px 0; }}
        h2 {{ color: #333; border-bottom: 2px solid #333; }}
        h3 {{ color: #666; }}
        pre {{ background: #f5f5f5; padding: 10px; overflow-x: auto; }}
    </style>
</head>
<body>
"""
            
            lines = content.split('\n')
            in_code_block = False
            
            for line in lines:
                if line.startswith('```'):
                    if in_code_block:
                        html_content += "</pre>\n"
                        in_code_block = False
                    else:
                        html_content += "<pre>\n"
                        in_code_block = True
                elif in_code_block:
                    html_content += line + "\n"
                elif line.startswith('## '):
                    html_content += f"<h2>{line[3:]}</h2>\n"
                elif line.startswith('### '):
                    html_content += f"<h3>{line[4:]}</h3>\n"
                elif line.startswith('!['):
                    # Handle images
                    match = re.match(r'!\[(.*?)\]\((.*?)\)', line)
                    if match:
                        alt_text, img_path = match.groups()
                        html_content += f'<img src="{img_path}" alt="{alt_text}" title="{alt_text}"><br>\n'
                elif line.startswith('- '):
                    html_content += f"<li>{line[2:]}</li>\n"
                elif line.startswith('**') and line.endswith('**'):
                    html_content += f"<strong>{line[2:-2]}</strong><br>\n"
                elif line.strip():
                    html_content += f"<p>{line}</p>\n"
                else:
                    html_content += "<br>\n"
            
            html_content += "\n</body>\n</html>"
            
            with open(html_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
                
        except Exception as e:
            print(f"Could not create HTML preview: {str(e)}")
    
    def _create_analysis_prompt(self, project_data: ProjectData, previous_logs: List[Dict], image_analyses: List[Dict]) -> str:
        logs_text = "\n".join([
            f"**{log['date']}:**\n{log['content']}\n"
            for log in previous_logs
        ])
        
        image_info = ""
        if image_analyses:
            image_info = f"\n**Image Analysis Results:**\n"
            for i, img_data in enumerate(image_analyses, 1):
                image_info += f"\n**Image {i}:** {img_data['path']}\n"
                image_info += f"Analysis: {img_data['analysis']}\n"
        
        return f"""
**Project Name:** {project_data.name}

**Project Description:** {project_data.description}

**Today's User Input:** {project_data.user_input}

**Date:** {project_data.current_date}

{image_info}

**Previous Logs (Last {len(previous_logs)} entries):**
{logs_text if logs_text else "No previous logs available."}

Based on this comprehensive information including visual evidence, analyze the current progress and provide insights.
"""
    
    def _create_log_generation_prompt(self, project_data: ProjectData, analysis: str, image_analyses: List[Dict], current_date: str) -> str:
        image_details = ""
        if image_analyses:
            image_details = "\n**Images to include in markdown:**\n"
            for i, img_data in enumerate(image_analyses, 1):
                image_details += f"- Image {i}: {img_data['relative_path']}\n"
                image_details += f"  Alt text: Project Screenshot {i}\n"
                image_details += f"  Analysis: {img_data['analysis'][:200]}...\n"
        
        return f"""
Generate a daily log entry for {current_date} based on:

**Project:** {project_data.name}
**Today's Input:** {project_data.user_input}
**Analysis:** {analysis}

{image_details}

IMPORTANT INSTRUCTIONS:
1. Create a comprehensive log entry with proper markdown structure
2. MUST include a "### Visual Evidence" section if images are provided
3. Use this exact format for images: ![Alt Text](relative_path)
4. Include image analysis as descriptions under each image
5. Reference visual evidence in other sections when relevant
6. Ensure all relative paths start with "./" for proper markdown display

Structure:
## {current_date}

### Progress Summary
[Brief overview referencing visual evidence if available]

### Tasks Completed
- [List completed tasks]

### Visual Evidence
[Include images with analysis - THIS SECTION IS MANDATORY if images exist]

### Challenges Faced
- [List any challenges or blockers]

### Next Steps
- [List planned next actions]

### Notes
[Any additional observations]
"""
    
    def process_project(
        self,
        project_name: str,
        project_description: str,
        user_input: str,
        username: str,
        current_date: str,
        images: List[str] = None
    ) -> Dict[str, Any]:
        """
        Main method to process project data and generate log with image analysis
        
        Args:
            project_name: Name of the project
            project_description: Description of the project
            user_input: Today's user input/update
            username: Username for file organization
            current_date: Date provided by user (YYYY-MM-DD format)
            images: List of image file paths (max 3)
        
        Returns:
            Dict with processing results
        """
        
        if images is None:
            images = []
        
        valid_images = [img for img in images if os.path.exists(img)][:3]
        
        json_file_path, md_file_path, _ = self._create_directory_structure(username)
        
        project_data = ProjectData(
            name=project_name,
            description=project_description,
            user_input=user_input,
            images=valid_images,
            log_file_path=md_file_path,
            json_file_path=json_file_path,
            username=username,
            current_date=current_date
        )
        
        initial_state = AgentState(
            project_data=project_data,
            previous_logs=[],
            current_log=None,
            image_analyses=[],
            previous_images=[],
            error=None
        )
        
        result = self.graph.invoke(initial_state)
        
        return {
            "success": result.get("success", False),
            "error": result.get("error"),
            "current_log": result.get("current_log"),
            "previous_logs_count": len(result.get("previous_logs", [])),
            "images_analyzed": len(result.get("image_analyses", [])),
            "json_file_path": json_file_path,
            "md_file_path": md_file_path,
            "date": current_date
        }

def generate_daily_log(project_name, project_description, user_input, username, current_date, image_paths=None):
    """
    Generate daily log with user-provided date and organized file structure
    
    Args:
        project_name: Name of the project
        project_description: Description of the project  
        user_input: Today's progress update
        username: Username for file organization
        current_date: Date in YYYY-MM-DD format
        image_paths: List of image file paths (optional)
    """
    if not GROQ_API_KEY:
        print("Please set GROQ_API_KEY")
        return
    
    agent = ProjectProgressAgent(GROQ_API_KEY)
    
    result = agent.process_project(
        project_name=project_name,
        project_description=project_description,
        user_input=user_input,
        username=username,
        current_date=current_date,
        images=image_paths or []
    )
    
    if result["success"]:
        print("✅ Log entry created successfully!")
        print(f"📁 JSON file: {result['json_file_path']}")
        print(f"📁 MD file: {result['md_file_path']}")
        print(f"📅 Date: {result['date']}")
        print(f"📊 Previous logs found: {result['previous_logs_count']}")
        print(f"🖼️ Images analyzed: {result['images_analyzed']}")
        print("\n📝 Generated log entry:")
        print("=" * 50)
        print(result["current_log"])
    else:
        print("❌ Error occurred:")
        print(result["error"])
    
    return result["current_log"]

def main():
    """Example usage of the Enhanced ProjectProgressAgent with user date"""
    
    if not GROQ_API_KEY:
        print("Please set GROQ_API_KEY")
        return
    
    result = generate_daily_log(
        project_name="AI-Powered Task Manager",
        project_description="Building a comprehensive task management application with AI features for priority suggestion and deadline prediction.",
        user_input="Today I worked on implementing the user authentication system. Successfully integrated OAuth with Google and GitHub. Also started working on the database schema design for tasks and user profiles. Facing some challenges with session management.",
        username="ayush",
        current_date="2025-12-15",
        image_paths=["C://Users//DC//Pictures//Screenshots//Screenshot (483).png"]
    )

# if __name__ == "__main__":
#     main()

