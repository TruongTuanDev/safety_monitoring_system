import tkinter as tk
from tkinter import ttk, messagebox
from typing import Optional
from auth.manager import authenticate_user, register_user


def show_auth_window(db_client) -> Optional[dict]:
    result = {'value': None}

    root = tk.Tk()
    root.title('User Authentication System')
    root.geometry('500x450')
    root.configure(bg='#f5f5f5')

    # Center window on screen
    window_width = 500
    window_height = 450
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    center_x = int(screen_width / 2 - window_width / 2)
    center_y = int(screen_height / 2 - window_height / 2)
    root.geometry(f'{window_width}x{window_height}+{center_x}+{center_y}')

    # Style configuration
    style = ttk.Style()
    style.theme_use('clam')

    # Configure colors
    style.configure('Title.TLabel',
                    font=('Segoe UI', 16, 'bold'),
                    background='#f5f5f5',
                    foreground='#2c3e50')

    style.configure('Subtitle.TLabel',
                    font=('Segoe UI', 10),
                    background='#f5f5f5',
                    foreground='#7f8c8d')

    style.configure('Input.TLabel',
                    font=('Segoe UI', 9, 'bold'),
                    background='#f5f5f5',
                    foreground='#34495e')

    style.configure('Primary.TButton',
                    font=('Segoe UI', 10, 'bold'),
                    padding=8)

    style.configure('Secondary.TButton',
                    font=('Segoe UI', 9),
                    padding=6)

    style.configure('Success.TLabel',
                    font=('Segoe UI', 9),
                    background='#f5f5f5',
                    foreground='#27ae60')

    style.configure('Error.TLabel',
                    font=('Segoe UI', 9),
                    background='#f5f5f5',
                    foreground='#e74c3c')

    # Create main container with scrollbar
    main_container = ttk.Frame(root)
    main_container.pack(fill='both', expand=True)

    # Create a canvas for scrolling
    canvas = tk.Canvas(main_container, bg='#f5f5f5', highlightthickness=0)
    scrollbar = ttk.Scrollbar(main_container, orient='vertical', command=canvas.yview)

    # Create scrollable frame
    scrollable_frame = ttk.Frame(canvas)

    # Configure the canvas
    scrollable_frame.bind(
        '<Configure>',
        lambda e: canvas.configure(scrollregion=canvas.bbox('all'))
    )

    canvas_frame_id = canvas.create_window((0, 0), window=scrollable_frame, anchor='nw')
    canvas.configure(yscrollcommand=scrollbar.set)

    # Pack canvas and scrollbar
    canvas.pack(side='left', fill='both', expand=True, padx=20, pady=10)
    scrollbar.pack(side='right', fill='y')

    # Bind mouse wheel for scrolling
    def _on_mousewheel(event):
        canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    canvas.bind_all('<MouseWheel>', _on_mousewheel)

    # Header
    header_frame = ttk.Frame(scrollable_frame)
    header_frame.pack(fill='x', pady=(0, 20))

    ttk.Label(header_frame,
              text='🔐 Authentication Portal',
              style='Title.TLabel').pack()

    ttk.Label(header_frame,
              text='Please login or register to continue',
              style='Subtitle.TLabel').pack(pady=(5, 0))

    # Notebook
    notebook = ttk.Notebook(scrollable_frame)
    notebook.pack(fill='both', expand=True, pady=(0, 20))

    # Configure notebook style
    style.configure('TNotebook.Tab',
                    font=('Segoe UI', 10, 'bold'),
                    padding=[15, 5])

    # --- Login Tab ---
    frame_login = ttk.Frame(notebook, padding=20)
    notebook.add(frame_login, text='Login')

    login_fields = ttk.Frame(frame_login)
    login_fields.pack(fill='both', expand=True)

    # Username
    ttk.Label(login_fields, text='Username:', style='Input.TLabel') \
        .grid(row=0, column=0, sticky='w', pady=(0, 5))
    login_user_var = tk.StringVar()
    login_user_entry = ttk.Entry(login_fields,
                                 textvariable=login_user_var,
                                 font=('Segoe UI', 10),
                                 width=35)
    login_user_entry.grid(row=0, column=1, pady=(0, 15), padx=(10, 0))
    login_user_entry.focus()

    # Password
    ttk.Label(login_fields, text='Password:', style='Input.TLabel') \
        .grid(row=1, column=0, sticky='w', pady=(0, 5))
    login_pass_var = tk.StringVar()
    login_pass_entry = ttk.Entry(login_fields,
                                 textvariable=login_pass_var,
                                 show='•',
                                 font=('Segoe UI', 10),
                                 width=35)
    login_pass_entry.grid(row=1, column=1, pady=(0, 20), padx=(10, 0))

    # Login button
    def on_login():
        username = login_user_var.get().strip()
        password = login_pass_var.get()

        if not username or not password:
            status_label.config(text='❌ Please fill all fields', style='Error.TLabel')
            return

        # Show loading state
        login_button.config(state='disabled', text='Logging in...')
        root.update()

        user = authenticate_user(db_client, username, password)

        if user:
            status_label.config(
                text=f'✅ Welcome back, {user.get("full_name", username)}!',
                style='Success.TLabel'
            )
            result['value'] = user
            root.after(1000, root.destroy)
        else:
            status_label.config(text='❌ Invalid username or password', style='Error.TLabel')
            login_button.config(state='normal', text='Login')

    login_button = ttk.Button(login_fields,
                              text='Login',
                              style='Primary.TButton',
                              command=on_login)
    login_button.grid(row=2, column=0, columnspan=2, pady=(10, 0))

    # Bind Enter key to login
    login_pass_entry.bind('<Return>', lambda e: on_login())

    # --- Register Tab ---
    frame_register = ttk.Frame(notebook, padding=20)
    notebook.add(frame_register, text='Register')

    # Create a frame inside register tab that can expand
    register_content = ttk.Frame(frame_register)
    register_content.pack(fill='both', expand=True)

    # Configure grid for register form
    for i in range(10):
        register_content.grid_rowconfigure(i, weight=1)
    register_content.grid_columnconfigure(1, weight=1)

    # Registration fields
    fields_config = [
        ('Username:', 'username', '', False, 0),
        ('Password:', 'password', '•', False, 1),
        ('Confirm Password:', 'confirm', '•', False, 2),
        ('Full Name:', 'fullname', '', True, 3),
        ('Age:', 'age', '', True, 4),
        ('Position:', 'position', '', True, 5),
        ('Email:', 'email', '', True, 6),
        ('Phone:', 'phone', '', True, 7)
    ]

    # Store variables
    reg_vars = {}

    for label_text, var_name, show_char, optional, row in fields_config:
        # Label
        ttk.Label(register_content, text=label_text, style='Input.TLabel') \
            .grid(row=row, column=0, sticky='w', pady=(0, 10))

        # Entry
        var = tk.StringVar()
        reg_vars[var_name] = var

        entry = ttk.Entry(register_content,
                          textvariable=var,
                          show=show_char,
                          font=('Segoe UI', 10),
                          width=35)
        entry.grid(row=row, column=1, pady=(0, 10), padx=(10, 0), sticky='ew')

        # Optional indicator
        if optional:
            ttk.Label(register_content,
                      text='(Optional)',
                      font=('Segoe UI', 8),
                      foreground='#95a5a6') \
                .grid(row=row, column=2, padx=(5, 0), pady=(0, 10), sticky='w')

    # Register button - placed at row 8 (after all fields)
    def on_register():
        # Get all values
        username = reg_vars['username'].get().strip()
        password = reg_vars['password'].get()
        confirm = reg_vars['confirm'].get()
        fullname = reg_vars['fullname'].get().strip() or None
        age = reg_vars['age'].get().strip() or None
        position = reg_vars['position'].get().strip() or None
        email = reg_vars['email'].get().strip() or None
        phone = reg_vars['phone'].get().strip() or None

        # Validation
        if not username or not password:
            status_label.config(text='❌ Username and password are required', style='Error.TLabel')
            return

        if len(username) < 3:
            status_label.config(text='❌ Username must be at least 3 characters', style='Error.TLabel')
            return

        if len(password) < 6:
            status_label.config(text='❌ Password must be at least 6 characters', style='Error.TLabel')
            return

        # Check password length (bytes) for bcrypt
        password_bytes = password.encode('utf-8')
        if len(password_bytes) > 72:
            status_label.config(
                text='❌ Password is too long. Maximum is approximately 48 characters.',
                style='Error.TLabel'
            )
            return

        if password != confirm:
            status_label.config(text='❌ Passwords do not match', style='Error.TLabel')
            return

        # Show loading state
        register_button.config(state='disabled', text='Registering...')
        root.update()

        # Register user
        ok = register_user(db_client, username, password, fullname, age, position, email, phone)

        if ok:
            status_label.config(text='✅ Registration successful! Logging in...', style='Success.TLabel')
            # Auto-login
            user = authenticate_user(db_client, username, password)
            if user:
                result['value'] = user
                root.after(1500, root.destroy)
        else:
            status_label.config(text='❌ Registration failed. Username may already exist.', style='Error.TLabel')
            register_button.config(state='normal', text='Register')

    register_button = ttk.Button(register_content,
                                 text='Register',
                                 style='Primary.TButton',
                                 command=on_register)
    register_button.grid(row=8, column=0, columnspan=3, pady=(20, 10))

    # Update canvas width when window is resized - SỬA LỖI Ở ĐÂY
    def update_canvas_width(event):
        canvas_width = event.width - 40  # Subtract padding
        canvas.itemconfigure(canvas_frame_id, width=canvas_width)

    canvas.bind('<Configure>', update_canvas_width)

    # --- Bottom Section ---
    bottom_frame = ttk.Frame(scrollable_frame)
    bottom_frame.pack(fill='x', pady=(10, 0))

    # Guest button
    def on_guest():
        if messagebox.askyesno('Continue as Guest',
                               'You will have limited access as a guest.\nContinue?'):
            result['value'] = {
                'username': 'guest',
                'full_name': 'Guest',
                'is_guest': True
            }
            root.destroy()

    ttk.Button(bottom_frame,
               text='Continue as Guest',
               style='Secondary.TButton',
               command=on_guest).pack(side='left', padx=(0, 10))

    # Status label
    status_label = ttk.Label(bottom_frame,
                             text='Ready',
                             style='Subtitle.TLabel')
    status_label.pack(side='right')

    # Function to clear status
    def clear_status(event=None):
        if status_label['text'] not in ['Ready', '']:
            status_label.config(text='Ready')

    # Bind focus events to clear status
    for entry in [login_user_entry, login_pass_entry]:
        entry.bind('<FocusIn>', clear_status)

    # Bind focus events for register entries
    for var_name in reg_vars:
        # Get the entry widget associated with each variable
        for child in register_content.winfo_children():
            if isinstance(child, ttk.Entry) and child.cget('textvariable') == str(reg_vars[var_name]):
                child.bind('<FocusIn>', clear_status)
                break

    # Set tab switching to clear status
    def on_tab_changed(event):
        clear_status()
        # Update canvas scroll region when tab changes
        canvas.configure(scrollregion=canvas.bbox('all'))

    notebook.bind('<<NotebookTabChanged>>', on_tab_changed)

    # Configure canvas scroll region initially
    root.update()
    canvas.configure(scrollregion=canvas.bbox('all'))

    # Make window resizable
    root.minsize(450, 400)

    # Run the application
    root.mainloop()

    return result['value']
