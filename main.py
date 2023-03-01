import io
from tkinter import *
import face_recognition
import imutils
from PIL import ImageTk, Image
import cv2
from dependencies import *
import win32api
import win32con
from tkinter import messagebox
import numpy as np
import sqlite3
from scipy import spatial

btn = [190, 222, 50, 248]
btn_color = (180, 180, 180)
img_taken = False


def adapt_array(arr):
    out = io.BytesIO()
    np.save(out, arr)
    out.seek(0)
    return sqlite3.Binary(out.read())


def convert_array(text):
    out = io.BytesIO(text)
    out.seek(0)
    return np.load(out)


def get_one_officer(select_id):
    conn = sqlite3.connect('registered.db', detect_types=sqlite3.PARSE_DECLTYPES)
    try:
        conn.execute('''CREATE TABLE registered
                 (labels TEXT PRIMARY KEY NOT NULL, encodings array NOT NULL);''')
        conn.commit()
    except:
        pass

    cursor = conn.execute("SELECT encodings from registered where labels = " + select_id)
    ret = cursor.fetchall()
    ret = list(zip(*ret))

    conn.close()
    try:
        return list(ret[0])[0]
    except:
        return None


def get_all_data():
    conn = sqlite3.connect('registered.db', detect_types=sqlite3.PARSE_DECLTYPES)
    try:
        conn.execute('''CREATE TABLE registered
                 (labels TEXT PRIMARY KEY NOT NULL, encodings array NOT NULL);''')
        conn.commit()
    except:
        pass

    cursor = conn.execute("SELECT labels, encodings from registered")
    ret = cursor.fetchall()
    ret = list(zip(*ret))

    kwg = None
    try:
        kwg = {"encodings": list(ret[1]), "names": list(ret[0])}
    except:
        kwg = {"encodings": [], "names": []}
    conn.close()

    return kwg


def insert_new_officer(new_id, new_encoder):
    conn = sqlite3.connect('registered.db', detect_types=sqlite3.PARSE_DECLTYPES)
    try:
        conn.execute('''CREATE TABLE registered
                     (labels TEXT PRIMARY KEY NOT NULL, encodings array NOT NULL);''')
        conn.commit()
    except:
        pass

    conn.execute("INSERT INTO registered (labels,encodings) \
              VALUES (?, ?)", (new_id, new_encoder))
    conn.commit()
    conn.close()


def update_officer_photo(new_id, new_decoder):
    conn = sqlite3.connect('registered.db', detect_types=sqlite3.PARSE_DECLTYPES)
    try:
        conn.execute('''CREATE TABLE registered
                     (labels TEXT PRIMARY KEY NOT NULL, encodings array NOT NULL);''')
        conn.commit()
    except:
        pass

    conn.execute("DELETE from registered where labels = " + new_id)
    conn.commit()
    conn.execute("INSERT INTO registered (labels,encodings) \
          VALUES (?, ?)", (new_id, new_decoder))
    conn.commit()
    conn.close()


def label_encoding(feats, enc, temp_frames):
    name = "Unknown"
    for i in range(len(feats["encodings"])):
        threshold = 0.04
        sim = spatial.distance.cosine(enc, feats["encodings"][i])
        if sim <= threshold:
            name = feats["names"][i]
            break

    if name == "Unknown":
        fls = 0
        for fr in temp_frames:
            name = "Unknown"
            encodings = face_recognition.face_encodings(fr[0], fr[1])
            for i in range(len(feats["encodings"])):
                threshold = 0.04
                sim = spatial.distance.cosine(encodings[0], feats["encodings"][i])
                if sim <= threshold:
                    name = feats["names"][i]
                    break
            if name != "Unknown":
                fls += 1
            if fls == 2:
                break

        if fls == 2:
            return False
        else:
            return True
    else:
        return False


def verify_face(imgg):
    data = get_all_data()

    rgb = cv2.cvtColor(imgg, cv2.COLOR_BGR2RGB)

    boxes = face_recognition.face_locations(rgb, model='hog')
    encodings = face_recognition.face_encodings(rgb, boxes)

    names = []
    for encoding in encodings:
        matches = face_recognition.compare_faces(data["encodings"], encoding)
        name = "Unknown"
        if True in matches:
            threshold = 0.05
            for (i, b) in enumerate(matches):
                if b:
                    sim = spatial.distance.cosine(encoding, data["encodings"][i])
                    if sim < threshold:
                        name = data["names"][i]
                        threshold = sim

        names.append(name)

    return names


def process_click(event, x, y, flags, params):
    global img_taken, btn_color
    # check if the click is within the dimensions of the button
    if event == cv2.EVENT_LBUTTONDOWN:
        if btn[0] < y < btn[1] and btn[2] < x < btn[3]:
            img_taken = True
    if event == cv2.EVENT_MOUSEMOVE:
        if btn[0] < y < btn[1] and btn[2] < x < btn[3]:
            win32api.SetCursor(win32api.LoadCursor(0, win32con.IDC_HAND))
            btn_color = (255, 255, 255)
        else:
            btn_color = (180, 180, 180)


def run():
    if my_string.get() == "" or my_string.get() is None:
        messagebox.showinfo("", "First, add your Military Number or Full Name")
        return
    b1_5 = Label(window, text="", fg='green', width=50)
    b1_5.place(x=50, y=500)

    global btn, btn_color, img_taken
    btn = [190, 222, 50, 248]
    btn_color = (180, 180, 180)
    img_taken = False

    save_frame = None
    ret = None
    check_frames = []
    check_cnt = 0

    vs = WebcamVideoStream(src=0).start()
    # fps = FPS().start()
    while True:
        frame = vs.read()
        if frame is None:
            ret = "Check Camera Cable..?"
            break
        frame = imutils.resize(frame, width=300)
        frame = cv2.flip(frame, 1)
        copy = frame.copy()

        if check_cnt >= 4:
            copy[btn[0]:btn[1], btn[2]:btn[3]] = btn_color
        cv2.putText(copy, 'Capture your Image', (67, 210), cv2.FONT_HERSHEY_DUPLEX, 0.5, (0, 0, 255), 1
                    , cv2.LINE_AA)

        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        boxes = face_recognition.face_locations(rgb, model='hog')
        if 1 >= len(boxes) > 0 and check_cnt < 6:
            check_cnt += 1
            check_frames.append([rgb, boxes])

        for (x, y, w, h) in boxes:
            cv2.rectangle(copy, (h, x), (y, w), (0, 255, 0), 2)

        if check_cnt >= 4:
            cv2.imshow("Register", copy)
            cv2.moveWindow("Register", 800, 50)
            btn_color = (180, 180, 180)
            cv2.setMouseCallback("Register", process_click)
            cv2.setWindowProperty("Register", cv2.WND_PROP_TOPMOST, 1)
            cv2.resizeWindow("Register", 300, 227)
            key = cv2.waitKey(1) & 0xFF

            if cv2.getWindowProperty("Register", cv2.WND_PROP_VISIBLE) < 1:
                ret = "Cancelled"
                break
        if img_taken:
            save_frame = frame
            break

    vs.stop()
    vs.stream.release()
    cv2.destroyAllWindows()

    if ret == "Check Camera Cable..?":
        messagebox.showinfo("Alert", "Check Camera Cable")
    elif ret == "Cancelled":
        pass
    else:
        rgb = cv2.cvtColor(save_frame, cv2.COLOR_BGR2RGB)
        boxes = face_recognition.face_locations(rgb, model='hog')
        encodings = face_recognition.face_encodings(rgb, boxes)

        sz = len(encodings)
        if sz == 0:
            messagebox.showinfo("", "ReCapture Your Image")
        elif sz == 1:
            data = get_all_data()

            flag = label_encoding(data, encodings[0], check_frames)

            if flag:
                cv2.imwrite(my_string.get() + '.jpg', save_frame)
                insert_new_officer(my_string.get(), encodings[0])
                messagebox.showinfo("", "Registration Done ")
            else:
                messagebox.showinfo("", "You are already registered")
        else:
            messagebox.showinfo("", "More than One Person has been Detected")


def test():
    b1_5 = Label(window, text="", fg='green', width=50)
    b1_5.place(x=50, y=500)

    vs = WebcamVideoStream(src=0).start()
    fps = FPS().start()
    ind = 1
    final_frame = None
    cam_err = 0

    while True:
        frame = vs.read()
        if frame is None:
            cam_err = 1
            break
        frame = imutils.resize(frame, width=300)
        frame = cv2.flip(frame, 1)
        copy = frame.copy()

        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        boxes = face_recognition.face_locations(rgb, model='hog')
        for (x, y, w, h) in boxes:
            cv2.rectangle(copy, (h, x), (y, w), (0, 255, 0), 2)

        cv2.putText(copy, 'Verifying...', (20, 20), cv2.FONT_ITALIC, 0.5, (0, 0, 255), 2, cv2.LINE_AA)
        cv2.imshow("Login_Scan", copy)
        cv2.moveWindow("Login_Scan", 850, 0)  # Move it to (40,30)
        cv2.setWindowProperty("Login_Scan", cv2.WND_PROP_TOPMOST, 1)
        cv2.resizeWindow("Login_Scan", 300, 227)
        key = cv2.waitKey(1) & 0xFF

        if cv2.getWindowProperty("Login_Scan", cv2.WND_PROP_VISIBLE) < 1:
            cam_err = 2
            break

        if ind % 40 == 0:
            final_frame = frame
            break
        ind += 1

    vs.stop()
    vs.stream.release()
    cv2.destroyAllWindows()
    if cam_err == 1:
        messagebox.showinfo("", "Check Camera Cable")
    elif cam_err == 2:
        pass
    else:
        cls = verify_face(final_frame)

        lbl = None
        sz = len(cls)
        if sz == 0:
            messagebox.showinfo("", "Can not clearly find You :<")
        elif sz == 1:
            lbl = cls[0]
            b1_5 = Label(window, text="You are " + lbl, fg='green', width=50)
            b1_5.place(x=50, y=500)
        else:
            lbl = cls[0]
            for i in range(1, sz):
                lbl = lbl + '$' + cls[i]
            b1_5 = Label(window, text="You are " + lbl, fg='green', width=50)
            b1_5.place(x=50, y=500)


# Converts np.array to TEXT when inserting
sqlite3.register_adapter(np.ndarray, adapt_array)
# Converts TEXT to np.array when selecting
sqlite3.register_converter("array", convert_array)

window = Tk()
window.geometry('450x600+400+300')
window.title('Program')
window.config(bg='wheat')
window.resizable(False, False)

my_string = StringVar()
Label(text='Face Recognition Demo', font=('Times New Roman', 14),
      fg='dark blue', background='green', foreground="white").pack()

Label(text='Enter Your National_ID or Full Name', font=('calibri', 11),
      fg='dark green').place(x=5, y=170)

Entry(window, textvariable=my_string, width=30).place(x=110, y=210)

b1_0 = Button(window, text="Image Capture", fg='green', command=run)
b1_0.place(x=205, y=240)

b1_1 = Button(window, text="Live Test", fg='green', command=test, width=50)
b1_1.place(x=50, y=400)

load = Image.open('design.jpg').resize((120, 120))
render = ImageTk.PhotoImage(load)
img = Label(window, image=render)
img.place(x=3, y=10)

window.mainloop()
