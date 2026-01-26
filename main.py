import datetime
import os
from tkinter import StringVar, IntVar

import dotenv
import ttkbootstrap as ttk
import tkinter.messagebox as msgbox
import requests as r
from escpos.constants import QR_ECLEVEL_M, QR_MODEL_2
from ttkbootstrap.widgets.scrolled import ScrolledFrame
from ttkbootstrap.widgets import ToastNotification

dotenv.load_dotenv(".env")

URL = os.getenv("HOST") +"/{}"


loginWindow = None
cookie = None

def login():
    global cookie
    # todo: perform login auth here
    response = r.post(URL.format("session"), json={'username': username_var.get(), 'password': password_var.get()})
    if response.status_code == 200:
        if response.json()['status'] == 'failed':
            msgbox.showerror(message="Incorrect username and password.", parent=loginWindow)
        else:
            loginWindow.destroy()
            cookie = response.cookies
            post_login()
    else:
        msgbox.showerror(message="Can't connect to the server.", parent=loginWindow)

def on_login_window_close():
    if not cookie:
        tk.destroy()

tk = ttk.Window()
tk.geometry("800x600")
tk.title("Import New Batch...")

style = ttk.Style()
style.configure(".", font=("Helvetica", 14))

"""LOGIN WINDOW"""

loginWindow = ttk.Toplevel(tk)
loginWindow.title("Login")
loginWindow.geometry("800x600")
loginWindow.lift(tk)

loginWindow.protocol("WM_DELETE_WINDOW", on_login_window_close)

username_var = ttk.StringVar(loginWindow)
password_var = ttk.StringVar(loginWindow)

# Declare login frame
loginFrame = ttk.Labelframe(loginWindow, text="Log In", padding=10)
username_label = ttk.Label(loginFrame, text="Username")
username_entry = ttk.Entry(loginFrame, textvariable=username_var)
password_label = ttk.Label(loginFrame, text="Password")
password_entry = ttk.Entry(loginFrame, show="*", textvariable=password_var)


btn = ttk.Button(loginFrame, text="Log In", command=login)

username_label.grid(column=0, row=0, padx=5, pady=5)
username_entry.grid(column=1, row=0,padx=5, pady=5)
password_label.grid(column=0, row=1,padx=5, pady=5)
password_entry.grid(column=1, row=1,padx=5, pady=5)

username_entry.focus()

btn.grid(column=0, row=2, columnspan=3, sticky='EW', pady=5)

loginFrame.pack(expand=1)

"""MAIN WINDOW"""

produce_list = []
chosen_produce_id = IntVar()
weight_input = StringVar()
quantity_input = StringVar()
harvest_date_input = StringVar()
hour_var = IntVar()
min_var = IntVar()
query = StringVar()

def update_produce_list(*args):
    show_produce_list(sf, produce_list, query.get())
query.trace_add('write', update_produce_list)

def show_produce_list(sf: ScrolledFrame, produce_list: list, filter = ""):
    for child in sf.winfo_children():
        child.destroy()
    for produce_id, produce in produce_list:
        if filter.lower() in produce.lower():
            ttk.Radiobutton(sf, text=produce, value=produce_id, variable=chosen_produce_id ).pack(anchor='w')

def post_login():
    global produce_list
    produce_list = get_produce_list()
    tk.focus()
    prodNameSearch.focus()
    hour_var.set(datetime.datetime.now().hour)
    min_var.set(datetime.datetime.now().minute)
    show_produce_list(sf, produce_list)

def get_produce_list():
    response = r.get(URL.format("api/produce/list-all-produces-simple"), cookies=cookie)

    if response.status_code == 200:
        return response.json()
    else:
        msgbox.showerror(parent=tk, message="Can't fetch produce list.")
        return []

def clear_fields():
    query.set("")
    chosen_produce_id.set(-1)
    weight_input.set("")
    quantity_input.set("")
    harvest_date.set_date(datetime.datetime.now())

    post_login()

def handle_new_batch():
    print(chosen_produce_id.get(), weight_input.get(), quantity_input.get(), harvest_date.get_date().timestamp())
    batchID = add_new_batch()
    if batchID:
        print (batchID)
        print_batch(int(batchID))
        clear_fields()

#       print_batch(batchID)

def print_batch(batchID):

    from escpos.printer import Usb
    import dotenv
    dotenv.load_dotenv(".env")

    try:
        p = Usb(
            int(os.getenv("VENDOR_ID"), base=16), int(os.getenv("PROD_ID"), base=16)
        )
        # p = Usb(hex(int(os.getenv("VENDOR_ID"))), os.getenv("PROD_ID"))
        p.qr(batchID, ec=QR_ECLEVEL_M, center=True, model=QR_MODEL_2, size=16)
        p.cut()
    except:
        msgbox.showerror(parent=tk, message="Printer not connected. New batch is still uploaded.")


def add_new_batch():

    if not weight_input.get() or not quantity_input.get():
        msgbox.showerror(parent=tk, message="One or more entries missing.")
        return False

    prod_id_exists = False
    for produce_id, produce in produce_list:

        if produce_id == chosen_produce_id.get():
            prod_id_exists = True
            break

    if not prod_id_exists:
        msgbox.showerror(parent=tk, message="Need to choose a produce type.")
        return False

    try:
        dt_object = harvest_date.get_date()
        dt_object.replace(hour=hour_var.get(), minute=min_var.get())

        d = r.post(URL.format("api/batch/new-batch"), json={
            "product_type_id": chosen_produce_id.get(),
            "weight": float(weight_input.get()),
            "quantity": int(quantity_input.get()),
            "import_datetime_utc_int": int(dt_object.timestamp() * 1000)
        }, cookies=cookie)
        if d.status_code != 200:
            if d.status_code == 406:
                msgbox.showerror(parent=tk, message="Creating new batch failed. Batch has conflicting storage requirements with other batches. Error: " + str(d.status_code))
            else:
                msgbox.showerror(parent=tk, message="Creating new batch failed. Error: " + str(d.status_code))
            return False
        else:
            print(d.json())
            return d.json()["id"]
    except Exception as e:
        msgbox.showerror(parent=tk, message="Cannot upload new record. Error: " + e.__str__())
        return False

uiFrame = ttk.Frame(tk, padding=10)

uiFrame.columnconfigure(0, minsize=150)
uiFrame.columnconfigure(1, weight=1)
uiFrame.columnconfigure(2, minsize=32)

ttk.Label(uiFrame, text='Add new batch', font=('Helvetica', 20, 'bold')).grid(column=0, row=0, columnspan=3, sticky='W' )
ttk.Label(uiFrame, text="Search produce name...", padding=(0, 5)).grid(column=0, row=1, sticky='WNS')

prodNameSearch = ttk.Entry(uiFrame, name='search', textvariable=query)
prodNameSearch.grid(column=0, row=2, columnspan=5, sticky='WE')


sf = ScrolledFrame(uiFrame, padding=10)
sf.grid(column=0, row=3, columnspan=5, sticky='WE')


ttk.Label(uiFrame, text="Weight (kg)").grid(column=0, row=4, sticky='WNS')
weight = ttk.Entry(uiFrame, textvariable=weight_input)
weight.grid(column=1, row=4, sticky='WE', pady=5, columnspan=5)

ttk.Label(uiFrame, text="Quantity").grid(column=0, row=5, sticky='WNS')
quantity = ttk.Entry(uiFrame, textvariable=quantity_input)
quantity.grid(column=1, row=5, sticky='WE', pady=5, columnspan=5)

ttk.Label(uiFrame, text="Harvest Date").grid(column=0, row=6, sticky='WNS')
harvest_date = ttk.DateEntry(uiFrame, dateformat=r'%Y-%m-%d')
harvest_date.grid(column=1, row=6, sticky='WE', pady=5)

hours_input = ttk.Spinbox(uiFrame, width=2, textvariable=hour_var, values=list(range(0, 24)), wrap=True)
hours_input.grid(column=2, row=6, sticky='WE', pady=5)
ttk.Label(uiFrame, text=":").grid(column=3, row=6)
minutes_input = ttk.Spinbox(uiFrame, width=2, textvariable=min_var, values=list(range(0, 60)), wrap=True)
minutes_input.grid(column=4, row=6, sticky='WE', pady=5)


btnOk = ttk.Button(uiFrame, text="Upload", bootstyle="success", command=handle_new_batch)
btnOk.grid(column=0, row=7, sticky='WE', pady=5, columnspan=5)
btnCancel = ttk.Button(uiFrame, text="Clear", bootstyle="danger", command=clear_fields)
btnCancel.grid(column=0, row=8, sticky='WE', pady=5, columnspan=5)

uiFrame.pack(fill="both", padx=10, pady=10)

btnrefresh = ttk.Button(uiFrame, text="Refresh Produce List", padding=(0, 5), command=post_login)
btnrefresh.grid(column=0, row=9, sticky='WE', columnspan=5)

# rearrange focus order
weight.lift(prodNameSearch)
quantity.lift(weight)
harvest_date.lift(quantity)
btnOk.lift(harvest_date)
btnCancel.lift(btnOk)
btnrefresh.lift(btnCancel)
tk.mainloop()