import tkinter as tk
from tkinter import ttk, messagebox
import json
import os

class AgendaBuilder:
    def __init__(self, root):
        self.root = root
        self.root.title("📋 Agenda JSON Builder")

        self.agenda = {
            "agenda_id": "new_agenda",
            "start_node": "",
            "nodes": {}
        }

        self.build_ui()

    def build_ui(self):
        frame = ttk.Frame(self.root, padding=10)
        frame.pack(fill="both", expand=True)

        # Agenda ID and Start Node
        ttk.Label(frame, text="Agenda ID:").grid(row=0, column=0, sticky="w")
        self.agenda_id_entry = ttk.Entry(frame)
        self.agenda_id_entry.insert(0, "onboarding_questionnaire")
        self.agenda_id_entry.grid(row=0, column=1, columnspan=3, sticky="ew")

        ttk.Label(frame, text="Start Node ID (e.g. q1):").grid(row=1, column=0, sticky="w")
        self.start_node_entry = ttk.Entry(frame)
        self.start_node_entry.grid(row=1, column=1, columnspan=3, sticky="ew")

        # Node Input
        ttk.Separator(frame).grid(row=2, columnspan=4, pady=5, sticky="ew")

        self.node_id_entry = self._labeled_entry(frame, "Node ID (e.g. q1):", 3, "Unique ID for this question")
        self.prompt_entry = self._labeled_entry(frame, "Prompt to show user:", 4, "e.g. 'What is your name?'")

        # Question Type
        ttk.Label(frame, text="Question Type:").grid(row=5, column=0, sticky="w")
        self.type_var = tk.StringVar(value="None")
        type_dropdown = ttk.Combobox(frame, textvariable=self.type_var, values=["None", "text", "choice", "end"], state="readonly")
        type_dropdown.grid(row=5, column=1, sticky="ew")
        type_dropdown.bind("<<ComboboxSelected>>", self.on_type_change)

        # Function Selection
        ttk.Label(frame, text="Special Function (optional):").grid(row=5, column=2, sticky="w")
        self.func_var = tk.StringVar(value="None")
        self.func_dropdown = ttk.Combobox(
            frame,
            textvariable=self.func_var,
            values=["None", "File Upload", "Send Email", "Thank You"],
            state="readonly"
        )
        self.func_dropdown.grid(row=5, column=3, sticky="ew")

        self.next_entry = self._labeled_entry(frame, "Next Node ID:", 6, "e.g. q2 (leave blank for 'end' type)")
        self.choices_entry = self._labeled_entry(frame, "Choices (comma-separated):", 7, "e.g. yes,no — for choice type")
        self.on_response_entry = self._labeled_entry(frame, "on_response (choice:node):", 8, "e.g. yes:q2,no:q3")

        self.timeout_entry = self._labeled_entry(frame, "Timeout (seconds, optional):", 9, "")
        self.reminder_entry = self._labeled_entry(frame, "Reminder (seconds, optional):", 10, "")

        ttk.Button(frame, text="➕ Add Node", command=self.add_node).grid(row=11, column=0, columnspan=4, pady=5)

        # Save Button
        ttk.Separator(frame).grid(row=12, columnspan=4, pady=5, sticky="ew")
        ttk.Button(frame, text="📅 Save as agenda.json", command=self.save_agenda).grid(row=13, column=0, columnspan=4)

        frame.columnconfigure(1, weight=1)
        frame.columnconfigure(3, weight=1)

    def _labeled_entry(self, frame, label, row, placeholder):
        ttk.Label(frame, text=label).grid(row=row, column=0, sticky="w")
        entry = ttk.Entry(frame)
        entry.insert(0, placeholder)
        entry.grid(row=row, column=1, columnspan=3, sticky="ew")
        entry.bind("<FocusIn>", lambda e: entry.delete(0, tk.END) if entry.get() == placeholder else None)
        return entry

    def on_type_change(self, event=None):
        is_end = self.type_var.get() == "end"
        for widget in [self.next_entry, self.choices_entry, self.on_response_entry]:
            state = "disabled" if is_end else "normal"
            widget.config(state=state)

    def add_node(self):
        node_id = self.node_id_entry.get().strip()
        if not node_id:
            messagebox.showerror("Error", "Node ID is required.")
            return

        node_data = {}

        # Function-first logic
        selected_func = self.func_var.get()
        if selected_func == "File Upload":
            from functions.file_upload import prompt_file_upload
            node_data.update(prompt_file_upload())
        elif selected_func == "Send Email":
            from functions.send_email import send_email_prompt
            node_data.update(send_email_prompt())
        elif selected_func == "Thank You":
            from functions.conclude_thank_you import conclude_with_thank_you
            node_data.update(conclude_with_thank_you())

        # Merge manual type if provided
        node_type = self.type_var.get().strip()
        if node_type != "None":
            node_data["type"] = node_type
            prompt_val = self.prompt_entry.get().strip()
            if prompt_val:
                node_data["prompt"] = prompt_val

            if node_type == "text":
                next_val = self.next_entry.get().strip()
                if next_val:
                    node_data["next"] = next_val
                node_data["on_response"] = "update_" + node_id

            elif node_type == "choice":
                choices = [c.strip() for c in self.choices_entry.get().split(",") if c.strip()]
                node_data["choices"] = choices
                on_response = {}
                for pair in self.on_response_entry.get().split(","):
                    if ":" in pair:
                        k, v = pair.strip().split(":")
                        on_response[k.strip()] = v.strip()
                node_data["on_response"] = on_response

        # Add prompt, next, timeout, reminder even for function-only nodes
        prompt_val = self.prompt_entry.get().strip()
        if prompt_val:
            node_data["prompt"] = prompt_val
        next_val = self.next_entry.get().strip()
        if next_val:
            node_data["next"] = next_val

        if self.timeout_entry.get().strip().isdigit():
            node_data["timeout"] = int(self.timeout_entry.get().strip())
        if self.reminder_entry.get().strip().isdigit():
            node_data["reminder"] = int(self.reminder_entry.get().strip())

        # Validate function with required next
        if selected_func in ["File Upload", "Send Email"] and "next" not in node_data:
            messagebox.showwarning("Warning", f"A 'next' node is required for the '{selected_func}' function.")

        self.agenda["nodes"][node_id] = node_data

        if not self.agenda["start_node"]:
            self.start_node_entry.insert(0, node_id)

        messagebox.showinfo("Success", f"✅ Node '{node_id}' added to agenda.")

        for entry in [self.node_id_entry, self.prompt_entry, self.next_entry,
                      self.choices_entry, self.on_response_entry,
                      self.timeout_entry, self.reminder_entry]:
            entry.delete(0, tk.END)

    def save_agenda(self):
        self.agenda["agenda_id"] = self.agenda_id_entry.get().strip()
        self.agenda["start_node"] = self.start_node_entry.get().strip()
        with open("agenda.json", "w") as f:
            json.dump(self.agenda, f, indent=2)
        messagebox.showinfo("Saved", "📅 Agenda saved as agenda.json")

# === Run the App ===
if __name__ == "__main__":
    root = tk.Tk()
    app = AgendaBuilder(root)
    root.mainloop()
