# pip install azure-ai-projects==1.0.0b10
from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential

project_client = AIProjectClient.from_connection_string(
    credential=DefaultAzureCredential(),
    conn_str="eastus.api.azureml.ms;a213f870-5e4a-4983-8cee-3b2fad145c5f;abp-eu1-sbx-rg-coe;testcasesgeneration")

agent = project_client.agents.get_agent("asst_LrYttLIEU8SHg29lVB3Mm8aT")

thread = project_client.agents.get_thread("thread_2j910jo1m8YF0ooPV4apZ3fJ")

message = project_client.agents.create_message(
    thread_id=thread.id,
    role="user",
    content="Hi PowerApps_Agent"
)

run = project_client.agents.create_and_process_run(
    thread_id=thread.id,
    agent_id=agent.id)
messages = project_client.agents.list_messages(thread_id=thread.id)

for text_message in messages.text_messages:
    print(text_message.as_dict())