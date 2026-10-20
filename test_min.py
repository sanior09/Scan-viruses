import tkinter as tk

def minimize():
    root.overrideredirect(False)
    root.iconify()

def on_map(event):
    if str(event.widget) == '.' and root.state() == 'normal':
        root.overrideredirect(True)

root = tk.Tk()
root.geometry("200x200")
root.overrideredirect(True)

btn = tk.Button(root, text="Minimize", command=minimize)
btn.pack(pady=50)

btn2 = tk.Button(root, text="Exit", command=root.destroy)
btn2.pack()

root.bind('<Map>', on_map)

root.after(5000, root.destroy) # close after 5s for testing
root.mainloop()
