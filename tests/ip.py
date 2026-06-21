import requests

try:
    response = requests.get('https://api.ipify.org?format=json', timeout=5)
    ip = response.json()['ip']
    print(f"Ваш внешний IP-адрес: {ip}")
except Exception as e:
    print(f"Ошибка получения IP: {e}")