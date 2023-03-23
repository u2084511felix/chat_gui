import openai
import sys
import os
import tkinter as tk
from tkinter import filedialog
from tkinter import messagebox


openai.api_key = "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"
Eqline = "====================================== \n"
idead_text_format = '''
'''
global project_name
global msg_array
global use_case


gpt_model = [ "gpt-3.5-turbo", "whisper-1", "text-davinci-edit-001", "text-embedding-ada-002", "babbage-similarity", "babbage-code-search-text", "curie-instruct-beta", "ada", "text-davinci-001", "babbage", "davinci", "babbage-code-search-code", "text-similarity-babbage-001", "code-search-babbage-text-001", "text-curie-001", "gpt-3.5-turbo-0301", "code-cushman-001", "code-search-babbage-code-001", "text-davinci-insert-001", "text-davinci-003", "code-davinci-002", "davinci-search-document", "code-davinci-edit-001" ]


def chat_gpt(text, index):
    #global msg_array
    global project_description
    global output_text
    global completion


    completion = openai.ChatCompletion.create(
        model=gpt_model[index],
        messages=[
            {"role": "system", "content": f"Project Name: {project_name}. Project Descriptions: {project_description}"},
            {"role": "user", "content": f"{text}"}
        ]
    )

    reply = completion.choices[0].message.content
    #msg_array = reply
    output_text = reply
    return reply.strip()

def chat_gpt2(text, mindex):
    #global msg_array
    global project_description
    global output_text
    response = openai.ChatCompletion.create(
        model=gpt_model[index],
        messages=[
            {"role": "system", "content": f"Project Name: {project_name}. Project Descriptions: {project_description}"},
            {"role": "user", "content": f"{text}"}
        ]
    )

    reply = response.choices[0].message.content
    #msg_array = reply
    output_text = reply
    return reply.strip()












def main():
    global index_model

    def on_submit():
        global project_description
        project_name = box1_entry.get()

        input_text = text_input.get("1.0", tk.END)
        response_text.delete("1.0", tk.END)
        project_description = prompt_input.get("1.0", tk.END)
        
        output_text = chat_gpt(input_text, index_model)

        response_text.insert(tk.END, output_text)
        
        export_button.config(state=tk.NORMAL)  # Enable the export button

    def on_export():
        # get parent directory for new folder and file
        parent_dir = filedialog.askdirectory(title="Select new directory location.")
        
        folder_name = box1_entry.get()

        # create new folder and file with the same name
        folder_path = os.path.join(parent_dir, folder_name)
        os.makedirs(folder_path, exist_ok=True)
        txt_file_path = os.path.join(folder_path, folder_name + ".txt")

        # write some sample text to the new file
        with open(txt_file_path, "w") as file:
            file.write(output_text)
        

        print(f"New folder and files created at: {folder_path}")


    # Create a variable to store the selected option
    selected_option = tk.StringVar(root)
    selected_option.set(gpt_model[0])  # Set the default value to the first option
    index_model = gpt_model.index(selected_option.get())


    # Create the dropdown menu
    dropdown_menu = tk.OptionMenu(root, selected_option, *gpt_model)

    # Create UI elements
    text_input = tk.Text(root, wrap=tk.WORD, height=10, width=60)
    text_input_label = tk.Label(root, text="Prompt:")
    submit_button = tk.Button(root, text="Submit", command=on_submit)
    response_text = tk.Text(root, wrap=tk.WORD, state=tk.NORMAL, height=10, width=60)
    response_text_label = tk.Label(root, text="Response:")
    export_button = tk.Button(root, text="Export", command=on_export, state=tk.DISABLED)
    prompt_input = tk.Text(root, wrap=tk.WORD, height=10, width=30)
    prompt_input_label = tk.Label(root, text="Project Description:")

    box1_label = tk.Label(root, text="ProjectName:")
    box1_entry = tk.Entry(root)
    box1_entry.insert(0, f"{project_name}")


    # Place UI elements in the window
    text_input_label.grid(row=0, column=0, sticky="w", padx=10, pady=10)
    text_input.grid(row=1, column=0, columnspan=2, sticky="nsew", padx=10, pady=10)

    prompt_input_label.grid(row=0, column=2, sticky="w", padx=10, pady=10)
    prompt_input.grid(row=1, column=2, columnspan=2, sticky="nsew", padx=10, pady=10)

    response_text_label.grid(row=2, column=0, sticky="w", padx=10, pady=10)
    response_text.grid(row=3, column=0, columnspan=2, sticky="nsew", padx=10, pady=10)

    submit_button.grid(row=4, column=0, sticky="ew", padx=10, pady=10)
    export_button.grid(row=4, column=1, sticky="ew", padx=10, pady=10)

    dropdown_menu.grid(row=1, column=4, sticky="e", padx=10, pady=10)

    box1_label.grid(row=2, column=2, sticky='w', padx=10, pady=10)
    box1_entry.grid(row=2, column=3, sticky='e', padx=10, pady=10)

    # Configure grid weights
    root.grid_columnconfigure(0, weight=1)
    root.grid_columnconfigure(1, weight=1)
    root.grid_columnconfigure(2, weight=1)
    root.grid_columnconfigure(3, weight=1)
    root.grid_columnconfigure(4, weight=1)
    root.grid_rowconfigure(0, weight=0)
    root.grid_rowconfigure(1, weight=1)
    root.grid_rowconfigure(2, weight=0)
    root.grid_rowconfigure(3, weight=1)
    root.grid_rowconfigure(4, weight=0)


    root.mainloop()


if __name__ == "__main__":
    root = tk.Tk()
    root.geometry("1000x600")
    project_name = tk.simpledialog.askstring(title="", prompt="Project Name: ")
    root.title(f"{project_name}")
    main()