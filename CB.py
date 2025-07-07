import json
import os
import tkinter as tk
from tkinter import filedialog

# === Load Agenda from File ===
def load_agenda(filename="agenda.json"):
    with open(filename, "r") as f:
        return json.load(f)

# === Build Decision Tree Map ===
def build_decision_tree_map(dynamic_tree):
    nodes = dynamic_tree["nodes"]
    decision_map = {}

    for node_id, node in nodes.items():
        entry = {
            "prompt": node.get("prompt", ""),
            "type": node.get("type", "text"),
            "next_nodes": [],
            "prev_nodes": []
        }

        if node["type"] == "choice":
            nexts = list(node.get("on_response", {}).values())
            entry["next_nodes"].extend(nexts)
        elif "next" in node:
            entry["next_nodes"].append(node["next"])

        decision_map[node_id] = entry

    for nid, info in decision_map.items():
        for next_id in info["next_nodes"]:
            if next_id in decision_map:
                decision_map[next_id]["prev_nodes"].append(nid)

    return decision_map

# === Save Metadata ===
def save_metadata_json(decision_map, filename="decision_tree_metadata.json"):
    with open(filename, "w") as f:
        json.dump(decision_map, f, indent=2)

# === Query Helpers ===
def get_next_nodes(node_id, decision_map):
    return decision_map.get(node_id, {}).get("next_nodes", [])

def get_prev_nodes(node_id, decision_map):
    return decision_map.get(node_id, {}).get("prev_nodes", [])

# === File Upload Handler ===
def handle_file_upload():
    print("📤 Opening file picker...")
    root = tk.Tk()
    root.withdraw()
    file_path = filedialog.askopenfilename(title="Select a file to upload")
    root.update()
    root.destroy()

    if file_path:
        print(f"✅ File selected: {file_path}")
        return file_path
    else:
        print("❌ No file selected.")
        return None

# === Display Choices Nicely ===
def display_choices(choices):
    for idx, choice in enumerate(choices, start=1):
        print(f"{idx}. {choice}")
    while True:
        user_input = input("👉 Your choice: ").strip()
        if user_input in choices:
            return user_input
        elif user_input.isdigit():
            index = int(user_input) - 1
            if 0 <= index < len(choices):
                return choices[index]
        print("❌ Invalid input. Try again.")

# === Chatbot Interaction ===
def run_chatbot(dynamic_tree):
    current_node_id = dynamic_tree["start_node"]
    nodes = dynamic_tree["nodes"]

    print("\n🤖 Chatbot Started. Type 'exit' to quit at any time.\n")
    responses = {}

    while True:
        if current_node_id not in nodes:
            print(f"❌ Node '{current_node_id}' not found.")
            break

        node = nodes[current_node_id]
        prompt = node["prompt"]
        node_type = node["type"]

        print(f"\n🧠 {prompt}")

        if node_type == "end":
            print("✅ Process complete.")
            break

        if node_type == "text":
            user_input = input("👉 Your response: ").strip()
            if user_input.lower() == "exit":
                print("👋 Exiting chatbot.")
                break
            responses[current_node_id] = user_input
            current_node_id = node.get("next")

        elif node_type == "choice":
            choices = node.get("choices", [])
            user_input = display_choices(choices)
            responses[current_node_id] = user_input
            next_map = node.get("on_response", {})
            current_node_id = next_map.get(user_input)

        elif node_type == "file_upload":
            file_path = handle_file_upload()
            responses[current_node_id] = file_path
            current_node_id = node.get("next")

        else:
            print(f"⚠️ Unsupported node type: {node_type}")
            break

    print("\n📝 Your Responses:")
    for k, v in responses.items():
        print(f"- {k}: {v}")

# === Main ===
if __name__ == "__main__":
    dynamic_tree = load_agenda("agenda.json")
    decision_map = build_decision_tree_map(dynamic_tree)
    save_metadata_json(decision_map, "decision_tree_metadata.json")
    print("✔ Loaded agenda and saved metadata.")

    while True:
        action = input("\nType 'chat' to run the chatbot, 'query' to inspect a node, or 'exit' to quit: ").strip().lower()
        if action == "exit":
            break

        elif action == "chat":
            run_chatbot(dynamic_tree)

        elif action == "query":
            print("\n📍 Available nodes in this agenda:")
            node_list = list(decision_map.keys())
            for idx, nid in enumerate(node_list, 1):
                summary = decision_map[nid]["prompt"][:50].replace("\n", " ")
                print(f"{idx}. {nid} – {summary}")

            node_input = input("\n🔍 Enter the number or ID of the node you want to inspect: ").strip()
            selected_node_id = None

            if node_input.isdigit():
                idx = int(node_input) - 1
                if 0 <= idx < len(node_list):
                    selected_node_id = node_list[idx]
            elif node_input in decision_map:
                selected_node_id = node_input

            if selected_node_id:
                print(f"\n🔎 Node ID: {selected_node_id}")
                print(f"Prompt: {decision_map[selected_node_id]['prompt']}")
                print(f"Type: {decision_map[selected_node_id]['type']}")
                print(f"Next nodes: {get_next_nodes(selected_node_id, decision_map)}")
                print(f"Previous nodes: {get_prev_nodes(selected_node_id, decision_map)}")
            else:
                print("❌ Invalid selection.")

        else:
            print("❌ Unknown command. Use 'chat', 'query', or 'exit'.")
