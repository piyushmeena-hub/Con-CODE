import requests

with open('add_faces.py', 'rb') as f: # Just sending a dummy text file as photo to see if it catches error
    files = {"photo": ("dummy.jpg", f, "image/jpeg")}
    try:
        res = requests.post("http://localhost:8000/api/v1/attendance/verify_face", files=files)
        print("Status", res.status_code)
        print("Response", res.json())
    except Exception as e:
        print(e)
