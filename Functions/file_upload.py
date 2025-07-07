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
