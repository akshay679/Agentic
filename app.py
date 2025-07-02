from flask import Flask, request, jsonify
from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential
from langchain.chat_models import AzureChatOpenAI
from langchain.schema import SystemMessage, HumanMessage
from dotenv import load_dotenv
import os

# ------------------ Load Environment Variables ------------------
load_dotenv()  # Load from .env file

AZURE_ENDPOINT = os.getenv("AZURE_ENDPOINT")
AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY")
AZURE_OPENAI_COMPLETION_API_VERSION = os.getenv("AZURE_OPENAI_COMPLETION_API_VERSION")
COMPLETION_MODEL = os.getenv("COMPLETION_MODEL")

AZURE_PROJECT_CONN_STR = os.getenv("AZURE_PROJECT_CONN_STR")
AGENT_MAP = {
    "powerbi": os.getenv("AGENT_POWERBI_ID"),
    "powerapps": os.getenv("AGENT_POWERAPPS_ID")
}

# ------------------ Initialize Flask ------------------
app = Flask(__name__)

# ------------------ Initialize Azure Foundry ------------------
project_client = AIProjectClient.from_connection_string(
    credential=DefaultAzureCredential(),
    conn_str=AZURE_PROJECT_CONN_STR
)

# ------------------ Initialize Azure OpenAI (LangChain) ------------------
def LLM_call():
    llm = AzureChatOpenAI(
        deployment_name=COMPLETION_MODEL,
        openai_api_key=AZURE_OPENAI_API_KEY,
        azure_endpoint=AZURE_ENDPOINT,
        openai_api_version=AZURE_OPENAI_COMPLETION_API_VERSION
    )
    return llm

llm = LLM_call()

# ------------------ Tool Classifier ------------------
def classify_tool_gpt(question: str) -> str:
    system_msg = SystemMessage(
        content=("You are an intelligent tool classifier. Based on the user's question, classify whether it relates to Power BI or Power Apps.\n"
            "Return ONLY one word: 'powerbi' or 'powerapps'.\n\n"
            "Examples:\n"
            "- 'Create a canvas app' → powerapps\n"
            "- 'Schedule a report refresh' → powerbi\n"
            "- 'Form to log issues' → powerapps\n"
            "- 'Visualize monthly sales' → powerbi"
        )
    )
    user_msg = HumanMessage(content=question)

    try:
        result = llm.invoke([system_msg, user_msg])
        label = result.content.strip().lower()
        if label in ["powerbi", "powerapps"]:
            return label
    except Exception as e:
        print("LLM classification error:", e)

    return None

def determine_agent(question: str) -> str:
    classification = classify_tool_gpt(question)
    if classification:
        return AGENT_MAP.get(classification)
    return None

# ------------------ Flask Route ------------------
@app.route('/',methods=['GET'])
def home():
    return jsonify({"responses": "Welcome"})

@app.route('/test',methods=['POST'])
def test():
    return jsonify({"Test": request.json.get("question")})

@app.route('/test2',methods=['GET'])
def test2():
    user_question = "What is Powerapps?"
    if not user_question:
        return jsonify({"error": "No question provided."}), 400

    agent_id = determine_agent(user_question)
    if not agent_id:
        return jsonify({"error": "Could not determine the correct agent from the question."}), 400

    try:
        agent = project_client.agents.get_agent(agent_id)
        thread = project_client.agents.create_thread()

        project_client.agents.create_message(
            thread_id=thread.id,
            role="user",
            content=user_question
        )

        project_client.agents.create_and_process_run(
            thread_id=thread.id,
            agent_id=agent.id
        )

        messages = project_client.agents.list_messages(thread_id=thread.id)
        responses = [msg.as_dict() for msg in messages.text_messages]

        return jsonify({"responses": responses})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/ask-agent', methods=['POST'])
def ask_agent():
    user_question = request.json.get("question")
    if not user_question:
        return jsonify({"error": "No question provided."}), 400

    agent_id = determine_agent(user_question)
    if not agent_id:
        return jsonify({"error": "Could not determine the correct agent from the question."}), 400

    try:
        agent = project_client.agents.get_agent(agent_id)
        thread = project_client.agents.create_thread()

        project_client.agents.create_message(
            thread_id=thread.id,
            role="user",
            content=user_question
        )

        project_client.agents.create_and_process_run(
            thread_id=thread.id,
            agent_id=agent.id
        )

        messages = project_client.agents.list_messages(thread_id=thread.id)
        responses = [msg.as_dict() for msg in messages.text_messages]

        return jsonify({"responses": responses})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ------------------ Run Flask App ------------------
if __name__ == '__main__':
    app.run(debug=True)