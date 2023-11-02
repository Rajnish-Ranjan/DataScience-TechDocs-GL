import requests

url = "http://127.0.0.1:8081/process_image"

files = {'image': ('vicode.jpeg', open('vicode.jpeg', 'rb'), 'image/png')}
data = {'output_file': 'certis.docx'}

response = requests.post(url, files=files, data=data)

print(response.status_code)
print(response.json())
