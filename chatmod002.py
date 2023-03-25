import tkinter as tk
from tkinter import ttk
import openai
from tkinter import filedialog

openai.api_key = "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"
Eqline = "====================================== \n"

gpt_model = ["gpt-3.5-turbo", "whisper-1", "text-davinci-edit-001", "text-embedding-ada-002", "babbage-similarity", "babbage-code-search-text", "curie-instruct-beta", "ada", "text-davinci-001", "babbage", "davinci", "babbage-code-search-code", "text-similarity-babbage-001", "code-search-babbage-text-001", "text-curie-001", "gpt-3.5-turbo-0301", "code-cushman-001", "code-search-babbage-code-001", "text-davinci-insert-001", "text-davinci-003", "code-davinci-002", "davinci-search-document", "code-davinci-edit-001"]

message_history = []
token_counter = 0

def chat(inp, role1, role2, index):
    global message_history
    global token_counter
    message_history.append({"role": role1, "content": f"{inp}"})
    completion = openai.ChatCompletion.create(
        model=gpt_model[index],
        messages=message_history,
    )
    reply_content = completion.choices[0].message.content
    message_history.append({"role": role2, "content": f"{reply_content}"})
    token_counter.set(completion.usage.total_tokens)
    return reply_content


def on_submit():
    input_text = text_input.get("1.0", tk.END).strip()
    #response_text.delete("1.0", tk.END)

    botreply = chat(input_text, role1_var.get(), role2_var.get(), model_var.get())
    #response_text.insert(tk.END, botreply)

    message_history_dropdown.config(state=tk.NORMAL)
    message_history_dropdown['menu'].delete(0, 'end')
    for i, msg in enumerate(message_history):
        message_history_dropdown['menu'].add_command(label=f"{i}", command=tk._setit(message_history_var, i, on_message_history_select))
    output_text.delete("1.0", tk.END)
    output_text.insert(tk.END, message_history[-1]['content'])


def on_message_history_select(value):
    output_text.delete("1.0", tk.END)
    output_text.insert(tk.END, message_history[value]['content'])


def on_message_history_clear():
    global message_history
    message_history = []
    message_history_dropdown['menu'].delete(0, 'end')


def on_model_change(event):
    model_var.set(gpt_model.index(model.get()))


def on_export():
    global message_history
    selectfile = filedialog.asksaveasfile(mode='w', defaultextension=".txt")
    with open(selectfile.name, "w") as f:
        f.write(str(message_history))

def on_import():
    global message_history
    selectfile = filedialog.askopenfile(mode='r', defaultextension=".txt")
    with open(selectfile.name, "r") as f:
        message_history = eval(f.read())
    message_history_dropdown.config(state=tk.NORMAL)
    message_history_dropdown['menu'].delete(0, 'end')
    for i, msg in enumerate(message_history):
        message_history_dropdown['menu'].add_command(label=f"{i}", command=tk._setit(message_history_var, i, on_message_history_select))

def on_role1_change(value):
    role1_var.set(value)

def on_role2_change(value):
    role2_var.set(value)

def on_submit_edit():
    global message_history
    global message_history_var
    global output_text

    edited_text = output_text.get("1.0", tk.END).strip()
    message_history[message_history_var.get()]['content'] = edited_text

def on_message_history_clear():
    global message_history
    message_history = []
    message_history_var.set(0)
    message_history_dropdown['menu'].delete(0, 'end')  # Clear dropdown menu items
    text_input.delete("1.0", tk.END)  # Clear text_input
    #response_text.delete("1.0", tk.END)  # Clear response_text
    output_text.delete("1.0", tk.END)  # Clear output_text


def main():
    global text_input
    global response_text
    global output_text
    global role1_var
    global role2_var
    global model_var
    global model
    global message_history_var
    global message_history_dropdown
    global selected_message
    global message_history
    global token_counter

    root = tk.Tk()
    root.title("Chatbot")
    root.geometry("800x600")

    tk.Label(root, text="Input:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
    text_input = tk.Text(root, height=11, width=70)
    text_input.grid(row=0, column=1, padx=5, pady=5)

    tk.Label(root, text="Msg_Editor:").grid(row=2, column=0, padx=5, pady=5, sticky=tk.W)
    output_text = tk.Text(root, height=11, width=70)
    output_text.grid(row=2, column=1, padx=5, pady=5)

    submit_button = ttk.Button(root, text="Submit", command=on_submit)
    submit_button.grid(row=0, column=4, padx=5, pady=5)

    submit_edit_button = ttk.Button(root, text="Submit Edit", command=on_submit_edit)
    submit_edit_button.grid(row=2, column=4, padx=5, pady=5)

    role1_var = tk.StringVar(root)
    role1_var.set("system")
    role1_dropdown = ttk.OptionMenu(root, role1_var, "user", *["user", "assistant", "system"], command=on_role1_change)
    tk.Label(root, text="Role 1:").grid(row=4, column=0, padx=5, pady=5, sticky=tk.W)
    role1_dropdown.grid(row=4, column=1, padx=5, pady=5, sticky=tk.W)

    role2_var = tk.StringVar(root)
    role2_var.set("user")
    role2_dropdown = ttk.OptionMenu(root, role2_var, "assistant", *["user", "assistant", "system"], command=on_role2_change)
    tk.Label(root, text="Role 2:").grid(row=5, column=0, padx=5, pady=5, sticky=tk.W)
    role2_dropdown.grid(row=5, column=1, padx=5, pady=5, sticky=tk.W)


    model_var = tk.IntVar(root)
    model_var.set(0)
    tk.Label(root, text="Model:").grid(row=6, column=0, padx=5, pady=5, sticky=tk.W)
    model = tk.StringVar(root)
    model.set(gpt_model[0])
    model_dropdown = ttk.OptionMenu(root, model, *gpt_model, command=on_model_change)
    model_dropdown.grid(row=6, column=1, padx=5, pady=5, sticky=tk.W)

    message_history_var = tk.IntVar(root)
    message_history_var.set(0)
    tk.Label(root, text="Message History:").grid(row=7, column=0, padx=5, pady=5, sticky=tk.W)
    message_history_dropdown = ttk.OptionMenu(root, message_history_var, '')
    message_history_dropdown.grid(row=7, column=1, padx=5, pady=5, sticky=tk.W)

    clear_history_button = ttk.Button(root, text="Clear History", command=on_message_history_clear)
    clear_history_button.grid(row=8, column=1, padx=5, pady=5, sticky=tk.W)

    export_button = ttk.Button(root, text="Export", command=on_export)
    export_button.grid(row=3, column=4, padx=5, pady=5, sticky=tk.W)


    import_button = ttk.Button(root, text="Import", command=on_import)
    import_button.grid(row=4, column=4, padx=5, pady=5, sticky=tk.W)

    #display token counter
    token_counter = tk.StringVar(root)
    token_counter.set("0")
    tk.Label(root, textvariable=token_counter).grid(row=7, column=4, padx=5, pady=5, sticky=tk.W)
    tk.Label(root, text="Tokens").grid(row=6, column=4, padx=5, pady=5, sticky=tk.W)

    root.mainloop()

if __name__ == "__main__":
    main()

